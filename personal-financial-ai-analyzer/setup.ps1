# Create .venv with Python 3.12 and install the pinned dependencies.
py -3.12 scripts\setup_environment.py
if ($LASTEXITCODE -ne 0) { Write-Error "Setup failed. Is Python 3.12 installed? See docs\installation_guide.md"; exit 1 }
