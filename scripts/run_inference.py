from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.inference.predictor import BackdoorPredictor


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run chip backdoor inference")
    parser.add_argument("--model-dir", default="models/codebert_chip_backdoor")
    parser.add_argument("--file", required=True)
    args = parser.parse_args()

    predictor = BackdoorPredictor(args.model_dir)
    result = predictor.predict_file(args.file)

    print(f"file={result.file_path}")
    print(f"has_backdoor={result.has_backdoor}")
    print(f"confidence={result.confidence:.4f}")
    print(f"backdoor_type={result.backdoor_type}")
    print(f"risk_level={result.risk_level}")
    print(f"suspicious_lines={result.suspicious_lines}")
