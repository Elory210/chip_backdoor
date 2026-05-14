from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

from .compiler_check import run_compile_check
from .schemas import DatasetPaths, SampleLabel
from .templates import build_base_code, inject_backdoor


EXT_MAP = {
    "verilog": ".v",
    "vhdl": ".vhd",
    "c": ".c",
    "cpp": ".cpp",
}


@dataclass
class GeneratorConfig:
    seed: int
    output_root: str
    sample_count: int
    backdoor_ratio: float
    split: Dict[str, float]
    languages: List[str]
    complexity_levels: List[str]
    scenarios: List[str]
    backdoor_types: List[str]
    stealth_levels: Dict[str, str]
    compiler_check: bool


class DatasetGenerator:
    def __init__(self, config_path: Path) -> None:
        with config_path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        self.cfg = GeneratorConfig(**raw)
        self.rng = random.Random(self.cfg.seed)

    def build(self) -> DatasetPaths:
        root = Path(self.cfg.output_root)
        paths = DatasetPaths(
            root=root,
            train_dir=root / "train",
            valid_dir=root / "valid",
            test_dir=root / "test",
            index_file=root / "index.csv",
            labels_file=root / "labels.jsonl",
        )
        for p in [paths.train_dir, paths.valid_dir, paths.test_dir]:
            p.mkdir(parents=True, exist_ok=True)

        labels = self._generate_labels(self.cfg.sample_count)
        self.rng.shuffle(labels)
        split_marks = self._split_marks(len(labels), self.cfg.split)

        rows: List[Dict[str, str]] = []
        with paths.labels_file.open("w", encoding="utf-8") as lj:
            for idx, label in enumerate(labels):
                split_name, split_dir = split_marks[idx]
                sample_name = f"sample_{idx:06d}{EXT_MAP[label.language]}"
                out_file = split_dir / sample_name

                base = build_base_code(label.language, f"{idx:06d}", label.complexity)
                code = inject_backdoor(base, label.language, label.backdoor_type)
                out_file.write_text(code, encoding="utf-8")

                if self.cfg.compiler_check and not run_compile_check(out_file, label.language):
                    out_file.unlink(missing_ok=True)
                    continue

                label.file_path = str(out_file.as_posix())
                row = label.to_row()
                row["split"] = split_name
                rows.append(row)
                lj.write(json.dumps(row, ensure_ascii=False) + "\n")

        self._write_index(paths.index_file, rows)
        return paths

    def _generate_labels(self, n: int) -> List[SampleLabel]:
        labels: List[SampleLabel] = []
        backdoor_count = int(n * self.cfg.backdoor_ratio)
        clean_count = n - backdoor_count

        for i in range(clean_count):
            lang = self.rng.choice(self.cfg.languages)
            comp = self.rng.choice(self.cfg.complexity_levels)
            scn = self.rng.choice(self.cfg.scenarios)
            labels.append(
                SampleLabel(
                    sample_id=f"clean_{i:06d}",
                    language=lang,
                    backdoor_type="none",
                    stealth_level="none",
                    complexity=comp,
                    scenario=scn,
                    has_backdoor=0,
                    file_path="",
                )
            )

        available_types = [t for t in self.cfg.backdoor_types if t != "none"]
        for i in range(backdoor_count):
            btype = self.rng.choice(available_types)
            lang = self.rng.choice(self.cfg.languages)
            comp = self.rng.choice(self.cfg.complexity_levels)
            scn = self.rng.choice(self.cfg.scenarios)
            labels.append(
                SampleLabel(
                    sample_id=f"bad_{i:06d}",
                    language=lang,
                    backdoor_type=btype,
                    stealth_level=self.cfg.stealth_levels[btype],
                    complexity=comp,
                    scenario=scn,
                    has_backdoor=1,
                    file_path="",
                )
            )
        return labels

    @staticmethod
    def _split_marks(total: int, split_cfg: Dict[str, float]) -> List[Tuple[str, Path]]:
        root = Path(split_cfg.get("_root", "."))
        train_n = int(total * split_cfg["train"])
        valid_n = int(total * split_cfg["valid"])
        marks: List[Tuple[str, Path]] = []
        marks.extend([("train", root / "train")] * train_n)
        marks.extend([("valid", root / "valid")] * valid_n)
        marks.extend([("test", root / "test")] * (total - train_n - valid_n))
        return marks

    @staticmethod
    def _write_index(index_file: Path, rows: List[Dict[str, str]]) -> None:
        if not rows:
            return
        index_file.parent.mkdir(parents=True, exist_ok=True)
        with index_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


def run_build(config_path: str) -> DatasetPaths:
    gen = DatasetGenerator(Path(config_path))
    gen.cfg.split["_root"] = gen.cfg.output_root
    return gen.build()
