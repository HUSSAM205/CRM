@echo off
REM Run all automated tests; the log is saved in logs\testing\
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" (
  echo Run START_HERE.bat or setup.bat first.
  if not defined PFA_NO_PAUSE pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\run_all_tests.py %*
set RC=%ERRORLEVEL%
if not defined PFA_NO_PAUSE pause
endlocal & exit /b %RC%
