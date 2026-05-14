from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict


@dataclass
class SampleLabel:
    sample_id: str
    language: str
    backdoor_type: str
    stealth_level: str
    complexity: str
    scenario: str
    has_backdoor: int
    file_path: str

    def to_row(self) -> Dict[str, str]:
        row = asdict(self)
        row["label_compact"] = (
            f"{self.language}_{self.backdoor_type}_{self.stealth_level}_"
            f"{self.complexity}_{self.scenario}_{self.has_backdoor}"
        )
        return row


@dataclass
class DatasetPaths:
    root: Path
    train_dir: Path
    valid_dir: Path
    test_dir: Path
    index_file: Path
    labels_file: Path
