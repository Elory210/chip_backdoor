from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.trainer import train


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train chip backdoor detector")
    parser.add_argument("--config", default="configs/train_config.yaml")
    args = parser.parse_args()

    model_dir, metrics = train(args.config)
    print(f"Model saved to: {model_dir}")
    print(f"Test metrics: {metrics}")
