@echo off
REM Create (or reuse) .venv with Python 3.12 and install the pinned dependencies. Never deletes data
REM or an existing environment.
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set "PY="
py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12"
if not defined PY (
  python -c "import sys; raise SystemExit(0 if sys.version_info[:2]==(3,12) else 1)" >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo Python 3.12 was not found.
  echo Install Python 3.12 64-bit from https://www.python.org/downloads/ and tick
  echo "Add python.exe to PATH" during installation. Then run START_HERE.bat again.
  if not defined PFA_NO_PAUSE pause
  exit /b 1
)
echo Using: %PY%
%PY% scripts\setup_environment.py
if errorlevel 1 (
  echo.
  echo Setup failed. Read the messages above; see docs\WINDOWS_INSTALLATION.md
  if not defined PFA_NO_PAUSE pause
  exit /b 1
)
echo.
echo Setup complete. Next: double-click START_HERE.bat (or run.bat).
if not defined PFA_NO_PAUSE pause
endlocal
