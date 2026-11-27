@echo off
REM Measure startup, page render, inference and memory on THIS computer (e.g. the student laptop).
REM Output: reports\laptop_benchmark.json (it contains no personal data).
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" (
  echo Run START_HERE.bat or setup.bat first.
  if not defined PFA_NO_PAUSE pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\audit\benchmark_master.py --label "student laptop" --out reports\laptop_benchmark.json
set RC=%ERRORLEVEL%
if not defined PFA_NO_PAUSE pause
endlocal & exit /b %RC%
