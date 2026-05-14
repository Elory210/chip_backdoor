python scripts/build_dataset.py --config configs/dataset_config.yaml
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python scripts/train_model.py --config configs/train_config.yaml
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Pipeline completed. You can now run desktop app."
