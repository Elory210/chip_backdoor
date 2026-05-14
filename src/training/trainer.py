from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import torch
import torch.nn.functional as F
import yaml
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from torch.optim import AdamW
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer

from .data import ChipDataset, load_split_records
from .model import MultiHeadBackdoorModel
from .simple_components import SimpleBackdoorModel, SimpleTokenizer


@dataclass
class TrainConfig:
    seed: int
    base_model: str
    max_length: int
    epochs: int
    batch_size: int
    learning_rate: float
    weight_decay: float
    early_stopping_patience: int
    dataset_root: str
    output_dir: str
    num_labels_binary: int
    num_labels_type: int


class FallbackTokenizerWrapper:
    def __init__(self, tokenizer: SimpleTokenizer) -> None:
        self.tokenizer = tokenizer

    def __call__(self, *args, **kwargs):
        return self.tokenizer(*args, **kwargs)

    def save_pretrained(self, save_directory: Path) -> None:
        self.tokenizer.save_pretrained(save_directory)


def _load_model_and_tokenizer(cfg: TrainConfig, dataset_root: Path, output_dir: Path):
    try:
        tokenizer = AutoTokenizer.from_pretrained(cfg.base_model, local_files_only=True)
        model = MultiHeadBackdoorModel(cfg.base_model, cfg.num_labels_binary, cfg.num_labels_type)
        model_kind = "transformer"
        return tokenizer, model, model_kind
    except Exception:
        texts = []
        for split in ("train", "valid", "test"):
            for record in load_split_records(dataset_root / "index.csv", split):
                texts.append(record.file_path.read_text(encoding="utf-8", errors="ignore"))
        tokenizer = SimpleTokenizer.build_from_texts(texts)
        model = SimpleBackdoorModel(len(tokenizer.vocab), hidden_size=128, num_labels_binary=cfg.num_labels_binary, num_labels_type=cfg.num_labels_type)
        model_kind = "simple"
        return FallbackTokenizerWrapper(tokenizer), model, model_kind


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def evaluate(model: MultiHeadBackdoorModel, loader: DataLoader, device: torch.device) -> Dict[str, float]:
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for batch in loader:
            ids = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            lbl = batch["label_binary"].to(device)

            logits_bin, _ = model(ids, mask)
            pred = torch.argmax(logits_bin, dim=-1)

            y_true.extend(lbl.cpu().tolist())
            y_pred.extend(pred.cpu().tolist())

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }


def _contrastive_penalty(binary_logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    probs = F.softmax(binary_logits, dim=-1)[:, 1]
    pos = probs[labels == 1]
    neg = probs[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return torch.tensor(0.0, device=binary_logits.device)
    return torch.relu(0.2 - (pos.mean() - neg.mean()))


def train(config_path: str) -> Tuple[Path, Dict[str, float]]:
    cfg_raw = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    cfg = TrainConfig(**cfg_raw)
    set_seed(cfg.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tokenizer, model, model_kind = _load_model_and_tokenizer(cfg, Path(cfg.dataset_root), out_dir)
    model = model.to(device)

    index_file = Path(cfg.dataset_root) / "index.csv"
    train_records = load_split_records(index_file, "train")
    valid_records = load_split_records(index_file, "valid")
    test_records = load_split_records(index_file, "test")
    train_ds = ChipDataset(train_records, tokenizer, cfg.max_length)
    valid_ds = ChipDataset(valid_records, tokenizer, cfg.max_length)
    test_ds = ChipDataset(test_records, tokenizer, cfg.max_length)

    train_loader = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True)
    valid_loader = DataLoader(valid_ds, batch_size=cfg.batch_size)
    test_loader = DataLoader(test_ds, batch_size=cfg.batch_size)

    optim = AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)

    best_valid = -1.0
    no_improve = 0
    history = []

    for epoch in range(cfg.epochs):
        model.train()
        total_loss = 0.0
        pbar = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{cfg.epochs}")
        for batch in pbar:
            ids = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            lbl_bin = batch["label_binary"].to(device)
            lbl_type = batch["label_type"].to(device)

            logit_bin, logit_type = model(ids, mask)
            loss_bin = F.cross_entropy(logit_bin, lbl_bin)
            loss_type = F.cross_entropy(logit_type, lbl_type)
            loss_ctr = _contrastive_penalty(logit_bin, lbl_bin)
            loss = loss_bin + 0.5 * loss_type + 0.1 * loss_ctr

            optim.zero_grad()
            loss.backward()
            optim.step()

            total_loss += float(loss.item())
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        valid_metrics = evaluate(model, valid_loader, device)
        avg_train_loss = total_loss / max(len(train_loader), 1)
        history.append({"epoch": epoch + 1, "train_loss": avg_train_loss, **valid_metrics})

        if valid_metrics["accuracy"] > best_valid:
            best_valid = valid_metrics["accuracy"]
            no_improve = 0
            torch.save(model.state_dict(), out_dir / "best_model.pt")
            tokenizer.save_pretrained(out_dir / "tokenizer")
        else:
            no_improve += 1
            if no_improve >= cfg.early_stopping_patience:
                break

    model.load_state_dict(torch.load(out_dir / "best_model.pt", map_location=device))
    test_metrics = evaluate(model, test_loader, device)

    cfg_raw["model_kind"] = model_kind
    (out_dir / "config.json").write_text(json.dumps(cfg_raw, indent=2), encoding="utf-8")
    (out_dir / "train_log.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    (out_dir / "test_metrics.json").write_text(json.dumps(test_metrics, indent=2), encoding="utf-8")

    return out_dir, test_metrics
