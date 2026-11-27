# Final Test Results (master audit 3)

| Run | Environment | Code | Passed | Failed | Skipped | Evidence |
|---|---|---|---|---|---|---|
| Baseline | dev, datasets present | `2eab394` + review doc edits | 196 | 0 | 0 | start of audit |
| **Final development run** | dev, CPython 3.12.3, Datasets A and B present | working tree (uncommitted master-audit-3 changes) | **223** | **0** | **0** | `logs/testing/pytest_20261127T133709Z.log` |
| **Fresh install** | clean copy of the tracked tree; `python3.12 scripts/setup_environment.py` (25 s); **no datasets** | same | **219** | **0** | **4** | `reports/master_audit_3/fresh_install/pytest_fresh.txt` |
| **Real browser** | Chromium (Playwright) against `run_application.py` on 127.0.0.1:8501 | same | **29/29 tasks** | 0 errors | — | `reports/ux_tasks/ux_task_results.json` (2026-11-27T13:33Z), `reports/screenshots/ux_*.png` |
| Phone width | iPhone 13 emulation, 8 pages | same | 8/8 without horizontal overflow | — | — | `reports/master_audit_3/mobile/` (empty-state pages) |
| Dependency audit | `pip-audit -r requirements.txt` | — | no known vulnerabilities | — | — | console, 2026-11-27 |
| Lint (changed files) | ruff 0.16.9, default rules | new and changed files | clean | — | — | console |

**Fresh-install skips** (data-dependent; each states its reason; never counted as passed):
* `test_data_leakage.py:37` and `:46`: splits not built;
* `test_data_leakage.py:56`: anomaly outputs not present;
* `test_reproducibility.py:31`: panel not built.

**Added in master audit 3 (196 → 223):**

| Tests | Count |
|---|---|
| `test_merge.py` | 6 |
| append/replace AppTest | 1 |
| `test_assistant_ma3.py` | 14 |
| forecast category | 1 |
| CSV formula guard | 1 |
| `test_launcher.py` | 2 |
| CRLF and Windows entry points | 2 |
| **Total added** | **27** |

**Browser tasks added:** 26–30:
* add a second file;
* replacement needs confirmation;
* highest-spending months;
* compare this month with last month;
* forecast type shown.

The original HW2 E4 run (12/12, 03:58 UTC, after 7 fix iterations) is preserved in git history and is not overwritten by this record.

**Not run:**
* **Windows** (no machine available);
* **laptop benchmark** (`benchmark.bat` must be run by the student);
* **human-participant usability study** (out of scope; every browser task is scripted).
