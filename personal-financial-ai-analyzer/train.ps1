# Resumable full pipeline: download, verify, audit, preprocess, train, evaluate, test.
$env:PYTHONUTF8 = "1"   # UTF-8 text I/O (Windows defaults to cp1252)
& .\.venv\Scripts\python.exe scripts\run_full_pipeline.py @args
