@echo off
REM Measure startup, page render, inference and memory on THIS computer (e.g. the student laptop).
REM Output: reports\laptop_benchmark.json  (send it back or commit it; it contains no personal data).
.venv\Scripts\python.exe scripts\audit\benchmark_master.py --label "student laptop" --out reports\laptop_benchmark.json
