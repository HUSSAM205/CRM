@echo off
REM Resumable full pipeline: download, verify, audit, preprocess, train, evaluate, test.
.venv\Scripts\python.exe scripts\run_full_pipeline.py %*
