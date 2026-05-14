from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from src.inference.predictor import PredictResult


def to_rows(results: Iterable[PredictResult]) -> list[dict]:
    rows = []
    for r in results:
        rows.append(
            {
                "file_path": r.file_path,
                "has_backdoor": r.has_backdoor,
                "confidence": round(r.confidence, 4),
                "backdoor_type": r.backdoor_type,
                "risk_level": r.risk_level,
                "suspicious_lines": ",".join(map(str, r.suspicious_lines)),
            }
        )
    return rows


def export_txt(results: Iterable[PredictResult], output_path: Path) -> None:
    lines = []
    for r in results:
        lines.extend(
            [
                f"File: {r.file_path}",
                f"Has backdoor: {r.has_backdoor}",
                f"Confidence: {r.confidence:.4f}",
                f"Type: {r.backdoor_type}",
                f"Risk: {r.risk_level}",
                f"Suspicious lines: {r.suspicious_lines}",
                "-" * 60,
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def export_excel(results: Iterable[PredictResult], output_path: Path) -> None:
    df = pd.DataFrame(to_rows(results))
    df.to_excel(output_path, index=False)
