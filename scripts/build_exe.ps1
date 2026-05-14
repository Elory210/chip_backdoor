Param(
  [string]$Entry = "scripts/run_desktop_app.py"
)

python -m pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name ChipBackdoorStudio $Entry
Write-Host "EXE generated under dist/ChipBackdoorStudio.exe"
