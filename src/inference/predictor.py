from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import torch
from transformers import AutoTokenizer

from src.training.data import TYPE2ID
from src.training.model import MultiHeadBackdoorModel
from src.training.simple_components import SimpleBackdoorModel, SimpleTokenizer


ID2TYPE = {v: k for k, v in TYPE2ID.items()}


@dataclass
class PredictResult:
    file_path: str
    has_backdoor: bool
    confidence: float
    backdoor_type: str
    risk_level: str
    suspicious_lines: List[int]


def detect_language(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".v":
        return "verilog"
    if ext in {".vhd", ".vhdl"}:
        return "vhdl"
    if ext == ".c":
        return "c"
    if ext in {".cc", ".cpp", ".cxx"}:
        return "cpp"
    return "unknown"


class BackdoorPredictor:
    def __init__(self, model_dir: str, base_model_name: str = "microsoft/codebert-base") -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_dir = Path(model_dir)
        config_path = self.model_dir / "config.json"
        model_path = self.model_dir / "best_model.pt"
        tok_dir = self.model_dir / "tokenizer"
        model_kind = "transformer"
        if config_path.exists():
            try:
                import json

                model_kind = json.loads(config_path.read_text(encoding="utf-8")).get("model_kind", "transformer")
            except Exception:
                model_kind = "transformer"

        if model_kind == "simple" and (tok_dir / "tokenizer.json").exists():
            self.tokenizer = SimpleTokenizer.from_pretrained(tok_dir)
            self.model = SimpleBackdoorModel(len(self.tokenizer.vocab), hidden_size=128, num_labels_binary=2, num_labels_type=len(TYPE2ID))
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(tok_dir if tok_dir.exists() else base_model_name, local_files_only=True)
            self.model = MultiHeadBackdoorModel(base_model_name, 2, len(TYPE2ID))

        try:
            state_dict = torch.load(model_path, map_location=self.device, weights_only=True)
        except TypeError:
            state_dict = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

    def predict_text(self, code: str, file_path: str = "") -> PredictResult:
        heuristic_type = self._heuristic_type(code)
        toks = self.tokenizer(
            code,
            truncation=True,
            padding="max_length",
            max_length=512,
            return_tensors="pt",
        )
        with torch.no_grad():
            logits_bin, logits_type = self.model(
                toks["input_ids"].to(self.device), toks["attention_mask"].to(self.device)
            )
            probs = torch.softmax(logits_bin, dim=-1)[0]
            pred_bin = int(torch.argmax(probs).item())
            conf = float(probs[pred_bin].item())
            pred_type = int(torch.argmax(logits_type, dim=-1).item())

        btype = ID2TYPE.get(pred_type, "none") if pred_bin == 1 else "none"
        if btype == "none" and heuristic_type != "none":
            btype = heuristic_type
            pred_bin = 1
            conf = max(conf, 0.6)
        elif heuristic_type == "none" and conf < 0.65:
            pred_bin = 0
            btype = "none"
        risk = "high" if btype in {"logic_tamper", "privilege_escalation"} else "medium"
        if btype == "none":
            risk = "low"

        return PredictResult(
            file_path=file_path,
            has_backdoor=bool(pred_bin),
            confidence=conf,
            backdoor_type=btype,
            risk_level=risk,
            suspicious_lines=self._locate_lines(code, btype),
        )

    def predict_file(self, path: str) -> PredictResult:
        p = Path(path)
        return self.predict_text(p.read_text(encoding="utf-8", errors="ignore"), str(p))

    @staticmethod
    def _locate_lines(code: str, btype: str) -> List[int]:
        keys = {
            "logic_tamper": ["hidden", "override", "tamper"],
            "privilege_escalation": ["auth", "bypass", "privilege", "root"],
            "data_exfiltration": ["leak", "copy", "send", "exfil", "assign leak", "trigger ="],
            "instruction_hijack": ["jump", "redirect", "hijack", "0xFF"],
            "none": [],
        }
        terms = keys.get(btype, [])
        if not terms:
            return []
        lines = []
        for i, line in enumerate(code.splitlines(), start=1):
            low = line.lower()
            if any(t.lower() in low for t in terms):
                lines.append(i)
        return lines[:20]

    @staticmethod
    def _heuristic_type(code: str) -> str:
        markers = {
            "logic_tamper": ["hidden", "override", "tamper"],
            "privilege_escalation": ["auth", "bypass", "privilege", "root"],
            "data_exfiltration": ["leak", "copy", "send", "exfil", "assign leak", "trigger =", "output wire leak"],
            "instruction_hijack": ["jump", "redirect", "hijack", "0xFF"],
        }
        score_by_type = {key: 0 for key in markers}
        low = code.lower()
        for btype, terms in markers.items():
            for term in terms:
                if term.lower() in low:
                    score_by_type[btype] += 1
        best_type = max(score_by_type, key=score_by_type.get)
        return best_type if score_by_type[best_type] > 0 else "none"

    def predict_batch(self, files: List[str]) -> List[PredictResult]:
        return [self.predict_file(f) for f in files]
