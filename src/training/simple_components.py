from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List

import torch
import torch.nn as nn


PAD_TOKEN = "[PAD]"
UNK_TOKEN = "[UNK]"


class SimpleTokenizer:
    def __init__(self, vocab: Dict[str, int]) -> None:
        self.vocab = vocab
        self.pad_token_id = vocab[PAD_TOKEN]
        self.unk_token_id = vocab[UNK_TOKEN]

    @classmethod
    def build_from_texts(cls, texts: Iterable[str], min_freq: int = 1) -> "SimpleTokenizer":
        counter: Counter[str] = Counter()
        for text in texts:
            counter.update(text)
        vocab = {PAD_TOKEN: 0, UNK_TOKEN: 1}
        for ch, freq in sorted(counter.items()):
            if freq >= min_freq and ch not in vocab:
                vocab[ch] = len(vocab)
        return cls(vocab)

    def __call__(self, text: str, truncation: bool, padding: str, max_length: int, return_tensors: str):
        ids = [self.vocab.get(ch, self.unk_token_id) for ch in text]
        ids = ids[:max_length]
        mask = [1] * len(ids)
        if padding == "max_length":
            while len(ids) < max_length:
                ids.append(self.pad_token_id)
                mask.append(0)
        input_ids = torch.tensor([ids], dtype=torch.long)
        attention_mask = torch.tensor([mask], dtype=torch.long)
        return {"input_ids": input_ids, "attention_mask": attention_mask}

    def save_pretrained(self, save_directory: Path) -> None:
        save_directory.mkdir(parents=True, exist_ok=True)
        (save_directory / "tokenizer.json").write_text(json.dumps(self.vocab, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def from_pretrained(cls, load_directory: str | Path) -> "SimpleTokenizer":
        vocab = json.loads(Path(load_directory, "tokenizer.json").read_text(encoding="utf-8"))
        return cls(vocab)


class SimpleBackdoorModel(nn.Module):
    def __init__(self, vocab_size: int, hidden_size: int, num_labels_binary: int, num_labels_type: int) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_size, padding_idx=0)
        self.encoder = nn.GRU(hidden_size, hidden_size, batch_first=True, bidirectional=True)
        self.dropout = nn.Dropout(0.2)
        self.binary_head = nn.Linear(hidden_size * 2, num_labels_binary)
        self.type_head = nn.Linear(hidden_size * 2, num_labels_type)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = self.embedding(input_ids)
        out, _ = self.encoder(x)
        mask = attention_mask.unsqueeze(-1).float()
        pooled = (out * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1.0)
        pooled = self.dropout(pooled)
        return self.binary_head(pooled), self.type_head(pooled)
