@echo off
REM Resumable full pipeline: download (1.6 GB), verify, audit, preprocess, train, evaluate, test.
REM NOT needed to use the dashboard: the trained models are already included.
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" (
  echo Run START_HERE.bat or setup.bat first.
  if not defined PFA_NO_PAUSE pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\run_full_pipeline.py %*
set RC=%ERRORLEVEL%
if not defined PFA_NO_PAUSE pause
endlocal & exit /b %RC%
