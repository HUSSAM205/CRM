@echo off
REM Start the dashboard at http://localhost:8501 (this computer only) and open the browser.
REM Uses the project's .venv Python directly (same effect as activating it).
REM Options: --port 8502   --strict-port   --no-browser
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
title Personal Financial AI Analyzer - running (close this window or run STOP.bat to stop)
if not exist ".venv\Scripts\python.exe" (
  echo The Python environment is missing. Double-click START_HERE.bat, or run setup.bat first.
  if not defined PFA_NO_PAUSE pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\run_application.py %*
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" echo The dashboard exited with an error (code %RC%). Read the messages above.
if "%RC%"=="0" echo The dashboard has stopped.
if not defined PFA_NO_PAUSE pause
endlocal & exit /b %RC%
