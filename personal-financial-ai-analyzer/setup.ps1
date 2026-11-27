# Create (or reuse) .venv with Python 3.12 and install the pinned dependencies. Never deletes data.
$env:PYTHONUTF8 = "1"   # UTF-8 text I/O (Windows defaults to cp1252)
Set-Location -Path $PSScriptRoot
$py = $null
try { & py -3.12 -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { $py = @("py", "-3.12") } } catch {}
if (-not $py) {
  try { & python -c "import sys; raise SystemExit(0 if sys.version_info[:2]==(3,12) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $py = @("python") } } catch {}
}
if (-not $py) { Write-Error "Python 3.12 was not found. Install Python 3.12 64-bit from python.org and tick 'Add python.exe to PATH'."; exit 1 }
Write-Host "Using: $($py -join ' ')"
$pyArgs = @()
if ($py.Length -gt 1) { $pyArgs = $py[1..($py.Length - 1)] }   # 1..0 would count DOWN in PowerShell
& $py[0] @pyArgs scripts\setup_environment.py
if ($LASTEXITCODE -ne 0) { Write-Error "Setup failed. Read the messages above; see docs\WINDOWS_INSTALLATION.md"; exit 1 }
