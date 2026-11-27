# Run all automated tests; log saved in logs\testing\
$env:PYTHONUTF8 = "1"   # UTF-8 text I/O (Windows defaults to cp1252)
& .\.venv\Scripts\python.exe scripts\run_all_tests.py @args
