# Measure startup, page render, inference and memory on THIS computer (e.g. the student laptop).
$env:PYTHONUTF8 = "1"   # UTF-8 text I/O (Windows defaults to cp1252)
& .\.venv\Scripts\python.exe scripts\audit\benchmark_master.py --label "student laptop" --out reports\laptop_benchmark.json
