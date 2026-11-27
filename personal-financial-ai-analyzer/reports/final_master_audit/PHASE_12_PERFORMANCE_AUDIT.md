# Phase 12: Performance and Robustness Audit

Status: **PARTIAL**. Measured on a cloud container (Intel Xeon @ 2.10 GHz, 4 vCPU, 16.9 GB, Linux, CPython 3.12.3). **Not on the student laptop.**

* **Application** (`performance_benchmarks.json`, 2026-11-27 12:02 UTC):
  * server start 0.92 s;
  * first page renders 0.12–1.18 s;
  * cold model loads 1.0–1.3 s;
  * warm inference: product forecast 4.1 ms, GBR 1.4 ms, unusual-transaction review 13.3 ms;
  * assistant 0.5–21 ms; Advisor 19 ms;
  * 200k-row CSV 0.39 s.
* **Peak memory:** ≤ 0.36 GB for the app paths.
* **Heavy jobs** (guarded, 4 GB hard limit):
  * Dataset B audit: 29.8M rows, 3.5 s, 1.56 GB;
  * E2-B: 60 s, 0.60 GB;
  * E3-B: 11.6 s, 0.50 GB;
  * earlier Dataset A jobs ≤ 1.86 GB.
* **Worker termination:** parent RSS 0.017 → 0.017 GB; system available 16.09 → 15.74 GB; no leftover worker processes (`worker_memory_release.json`).
* **Recovery after interruption:** partition resume reran only the deleted partitions and gave identical output (final audit A-07).
* **Laptop procedure:** `benchmark.bat` / `benchmark.ps1` writes `reports/laptop_benchmark.json` with the CPU model, RAM, Python version, dataset mode, startup, render, inference and peak memory. **Not executed:** no access to the laptop.
