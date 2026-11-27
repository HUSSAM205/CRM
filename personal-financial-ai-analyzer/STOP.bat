@echo off
REM Stop the dashboard started by START_HERE.bat / run.bat. Only this project's app is stopped.
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" (
  echo Nothing to stop: the application has not been set up on this computer.
  if not defined PFA_NO_PAUSE pause
  exit /b 0
)
".venv\Scripts\python.exe" scripts\stop_application.py
set RC=%ERRORLEVEL%
if not defined PFA_NO_PAUSE pause
endlocal & exit /b %RC%
