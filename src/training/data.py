from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import torch
from torch.utils.data import Dataset


TYPE2ID = {
    "none": 0,
    "logic_tamper": 1,
    "privilege_escalation": 2,
    "data_exfiltration": 3,
    "instruction_hijack": 4,
}


@dataclass
class Record:
    file_path: Path
    has_backdoor: int
    backdoor_type: str


class ChipDataset(Dataset):
    def __init__(self, records: List[Record], tokenizer, max_length: int) -> None:
        self.records = records
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        rec = self.records[idx]
        code = rec.file_path.read_text(encoding="utf-8", errors="ignore")
        toks = self.tokenizer(
            code,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        return {
            "input_ids": toks["input_ids"].squeeze(0),
            "attention_mask": toks["attention_mask"].squeeze(0),
            "label_binary": torch.tensor(rec.has_backdoor, dtype=torch.long),
            "label_type": torch.tensor(TYPE2ID[rec.backdoor_type], dtype=torch.long),
        }


def load_split_records(index_file: Path, split: str) -> List[Record]:
    out: List[Record] = []
    with index_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["split"] != split:
                continue
            out.append(
                Record(
                    file_path=Path(row["file_path"]),
                    has_backdoor=int(row["has_backdoor"]),
                    backdoor_type=row["backdoor_type"],
                )
            )
    return out
