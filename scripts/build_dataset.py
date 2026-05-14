from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset_gen.generator import run_build


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build chip backdoor dataset")
    parser.add_argument("--config", default="configs/dataset_config.yaml")
    args = parser.parse_args()

    paths = run_build(args.config)
    print(f"Dataset generated at: {paths.root}")
    print(f"Index: {paths.index_file}")
    print(f"Labels: {paths.labels_file}")
