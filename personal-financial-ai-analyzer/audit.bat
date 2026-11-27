@echo off
REM Read-only verification: dataset identity, manifest, full reconciliation, artifact reload, tests.
REM Requires data\raw\transactions_50M.parquet (run train.bat or scripts\download_dataset.py first).
.venv\Scripts\python.exe scripts\verify_dataset.py || exit /b 1
.venv\Scripts\python.exe scripts\audit\dataset_manifest.py || exit /b 1
.venv\Scripts\python.exe scripts\audit\reconcile_granular.py || exit /b 1
.venv\Scripts\python.exe scripts\verify_artifacts.py || exit /b 1
.venv\Scripts\python.exe scripts\run_all_tests.py
