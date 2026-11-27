# Launch the dashboard at http://localhost:8501 (local only). Options: --port 8502  --no-browser
$env:PYTHONUTF8 = "1"   # UTF-8 text I/O (Windows defaults to cp1252)
Set-Location -Path $PSScriptRoot
if (-not (Test-Path ".\.venv\Scripts\python.exe")) { Write-Error "The virtual environment is missing. Run setup.ps1 first."; exit 1 }
& .\.venv\Scripts\python.exe scripts\run_application.py @args
exit $LASTEXITCODE
