# User Manual

## 1. Build Dataset

Run:

```powershell
python scripts/build_dataset.py --config configs/dataset_config.yaml
```

Config fields in configs/dataset_config.yaml:

- sample_count
- backdoor_ratio
- languages
- compiler_check

## 2. Train Model

Run:

```powershell
python scripts/train_model.py --config configs/train_config.yaml
```

Model output directory: models/codebert_chip_backdoor/

## 3. Run Inference

Run:

```powershell
python scripts/run_inference.py --model-dir models/codebert_chip_backdoor --file tests/samples/demo_bad.c
```

## 4. Run Desktop App

Run:

```powershell
python scripts/run_desktop_app.py
```

Workflow:

1. Select files or folder.
2. Click Start Detection.
3. Check highlighted suspicious lines.
4. Export TXT or Excel report.

## 5. Troubleshooting

- Dependency missing: pip install -r requirements.txt
- Model file missing: train first and verify best_model.pt exists
- Empty results: ensure suffix is one of .v/.vhd/.vhdl/.c/.cpp
