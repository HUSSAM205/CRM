@echo off
REM Read-only verification: dataset identity, manifest, full reconciliation, artifact reload, tests.
REM Requires data\raw\transactions_50M.parquet (run train.bat or scripts\download_dataset.py first).
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" (
  echo Run START_HERE.bat or setup.bat first.
  if not defined PFA_NO_PAUSE pause
  exit /b 1
)
set RC=1
".venv\Scripts\python.exe" scripts\verify_dataset.py || goto :done
".venv\Scripts\python.exe" scripts\audit\dataset_manifest.py || goto :done
".venv\Scripts\python.exe" scripts\audit\reconcile_granular.py || goto :done
".venv\Scripts\python.exe" scripts\verify_artifacts.py || goto :done
".venv\Scripts\python.exe" scripts\run_all_tests.py && set RC=0
:done
if not "%RC%"=="0" echo Audit stopped at a failing step; read the messages above.
if not defined PFA_NO_PAUSE pause
endlocal & exit /b %RC%
