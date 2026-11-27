# Windows installation (status: NOT TESTED on Windows)

The scripts below exist and their Python dependencies were resolved for win_amd64 / CPython 3.12 with wheels only (`reports/verification/requirements-windows-resolved.txt`). **No Windows machine was available**, so none of these steps has been executed on Windows. Run them once and record the results.

Target: Windows laptop, Intel Core i7-1355U, 16 GB RAM, integrated graphics. No GPU is needed: every library is CPU-only.

| Step | Command (in `CRM\personal-financial-ai-analyzer`) | Expected outcome |
|---|---|---|
| 1. Python | install Python 3.12 64-bit from python.org, tick "Add to PATH" | `py -3.12 --version` prints 3.12.x |
| 2. Setup | `setup.bat` | ends with `Environment ready.` (Linux reference: 26 s) |
| 3. Tests | `test.bat` | 0 failed; without the dataset only the data-dependent tests skip, each with a stated reason (Linux fresh-clone count: `reports/final_master_audit/TEST_RESULTS.md`) |
| 4. App | `run.bat` | browser at http://localhost:8501; Transactions › "Load demo data" works on all 8 pages |
| 5. Data and training (optional, 1.6 GB) | `train.bat` | downloads, verifies the SHA-256, preprocesses in 50 partitions (each ≤ 4 GB), trains, evaluates. Resumable after interruption |
| 6. Audit (after step 5) | `audit.bat` | dataset identity PASS; reconciliation 9,488/9,488; artifacts PASS; tests pass |

**Step 7: laptop benchmark.** Run `benchmark.bat`. It writes `reports\laptop_benchmark.json` with the CPU model, RAM, Python version, dataset mode, server start, page render times, inference times and peak memory of each operation. It contains no personal data. That file closes HW1 P5. Never copy the container numbers into it.

The test count in step 3 is from the Linux fresh clone of the final commit (see `reports/final_master_audit/TEST_RESULTS.md` for the exact verified number).
