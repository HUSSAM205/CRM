# Windows Delivery Report (master audit 4)

* **Date:** 2026-11-27.
* **Environment:** a Linux cloud container (CPython 3.12.3, Chromium through Playwright). **No Windows machine was available, so no Windows execution is claimed.**

## Primary workflow

`START_HERE.bat` → setup when needed (reuses `.venv`, never overwrites it) → `run.bat` → server on 127.0.0.1:8501 → browser opens http://localhost:8501. Stop with `STOP.bat` or by closing the window.

## Defects found and fixed in this phase

| ID | Defect | Impact on Windows | Fix | Regression evidence |
|---|---|---|---|---|
| MA4-01 | 5 data workers and `benchmark_resources.py` imported `resource` (Unix only) | `train.bat` and `audit.bat` crash (ImportError) | `src/utils/peak_memory.py` (psutil `peak_wset` on Windows) | `test_no_unix_only_modules_outside_the_guarded_helper`, `test_peak_memory_falls_back_to_psutil_without_resource` |
| MA4-02 | 128 text reads and writes in 56 files had no `encoding=` | Windows defaults to cp1252: characters such as `≥ → − ×` in reports and docs fail or are garbled | `encoding="utf-8"` everywhere, plus `PYTHONUTF8=1` in every `.bat`, `.ps1` and the launcher's child process | `test_all_text_io_states_utf8` (AST scan) |
| MA4-03 | (in my own edit) the bulk encoding rewrite also changed the binary `"ab"`/`"wb"` download | the dataset download would raise ValueError, which the retry loop hides | reverted, and that call is documented as binary | `test_download_writes_binary_and_resumes` |
| MA4-04 | The launcher left its Streamlit server running when terminated (SIGTERM); 11 orphaned servers were found | a stale "already running" state; a port blocked | SIGTERM, SIGHUP and SIGBREAK are handled like Ctrl+C; the child is stopped, with a forced kill after 10 s | `test_terminating_the_launcher_leaves_no_orphaned_server` |
| MA4-05 | The STOP fallback scan could stop a dashboard the user is running while tests run | `test.bat` could close the user's app | Tests use an isolated record (`PFA_RUN_STATE`) and `--no-scan` | launcher tests |
| MA4-06 | `START_HERE.bat` and `STOP.bat` were not registered in git (caught by the fresh install) | a clone would lack the one-click scripts | registered; the completeness guard now covers `*.bat`, `*.ps1` and `.streamlit/config.toml` | `test_all_source_samples_fixtures_and_artifacts_are_tracked` |
| MA4-07 | The "all rows are completed" confirmation persisted from one file to the next | a second file's confirmation was implicit, or a click untoggled it | the checkbox is keyed per file fingerprint | `test_completed_confirmation_is_asked_again_for_each_new_file`; browser 31–32 |
| MA4-08 | `Path.rename` fails on Windows if the target exists | download finalisation | `Path.replace` | download test |
| MA4-09 | (in my own draft) one-line `(... & if ... pause & exit /b 1)` in the `.bat` files | the exit became part of the inner `if`, so the script continued without `.venv` | multi-line blocks | `test_batch_files_are_structurally_sound` |

## Added for practical use

| Addition | Where |
|---|---|
| One-click start | `START_HERE.bat` |
| Safe stop: verifies it is this project's process, stops it and its children | `STOP.bat` → `scripts/stop_application.py` |
| Automatic free port (8502–8510) if 8501 is taken; `--strict-port` | `scripts/run_application.py` |
| A launcher record (`.run/app.json`, git-ignored) to detect an already-running instance | same |
| Windows-friendly scripts: own folder, UTF-8 mode, pause on exit, `.venv` checks | all `.bat` files |
| Export of the filtered transactions as a formula-safe CSV | Transactions page |
| Synthetic personal demo: two overlapping TRY exports; walkthrough values computed by the engine | `data/samples/demo_personal_part*.csv`, `docs/DEMO_WALKTHROUGH.md` |
| Laptop verification checklist | `docs/WINDOWS_LAPTOP_VERIFICATION.md` |
| Windows wheel resolution (59 packages, wheels only, win_amd64 / cp312) | `reports/master_audit_4/requirements-windows-resolved.txt` |

## Test results (actual runs)

| Run | Passed | Failed | Skipped | Evidence |
|---|---|---|---|---|
| Full suite, development (datasets present) | **234** | 0 | 0 | `logs/testing/` (latest run) |
| Fresh install of the tracked tree (no datasets) | **230** | 0 | 4 (data-dependent; reasons stated) | `reports/master_audit_4/fresh_install/pytest_fresh.txt` |
| Real browser (Chromium) against the launcher on 127.0.0.1:8501 | **36/36 tasks** | 0 | — | `reports/ux_tasks/ux_task_results.json`, `reports/screenshots/ux_*.png` |
| Fresh install: start, duplicate start, STOP | healthy in 4 s; duplicate refused; stopped; record removed; 0 processes left | — | — | `fresh_install/launch.log`, `again.log` |
| Saved models without the dataset (fresh copy) | 8/8 reload | 0 | — | `verify_artifacts.py` |
| Dataset A identity | SHA-256 = live HF; 50,000,000 rows | — | — | `verify_dataset.py` OVERALL PASS |
| Experiments and artifacts | `git diff` of `reports/experiments` and `artifacts`: empty | — | — | git |
| Dependency vulnerabilities | none known | — | — | `pip-audit -r requirements.txt` |
| Secrets scan; files over 1 MB; tracked datasets | 0; 0; none (only `PROVENANCE.json`) | — | — | regex scan |

## Feature verification

| Area | Feature | Evidence |
|---|---|---|
| Analyzer | upload, preview, mapping, validation errors | browser 1–4, 14, 31 |
| | add a second file; duplicate handling; confirmed replacement | browser 26–27, 32; `test_merge.py` |
| | daily, weekly and monthly spending; categories; spending changes | `test_insights.py`, AppTests; browser 6, 17 |
| | income, expenses, cash flow; recurring payments | browser 5, 17, 33; walkthrough assistant answers |
| Advisor | profile, essential vs non-essential | browser 18; `test_advisor.py` |
| | savings goal, milestones, emergency fund | browser 18, 25, 36; unit tests |
| | scenarios; affordability; recommendations | browser 19, 20; unit tests |
| Predictive | HW2 E2 unchanged (shown as "Experimental"); E2-B labelled "Validated … synthetic Dataset B"; deterministic estimate labelled | browser 8, 23, 24, 30, 34; `reproduce_e2b.py` |
| Anomaly | amount, hour and rare-category reasons; "review recommended", never fraud | browser 9, 34, 35 |
| Assistant | supported questions; month comparison; highest months; recurring; remaining budget; savings rate; reliability; isolation; refusals | browser 10, 11, 21, 24, 28, 29, 35; `test_assistant*.py` |
| Settings and data | account and currency; retention; delete; export | browser 5, 12, 13, 22, 37; unit tests |

**Not verified:**
* any execution on Windows or on the student laptop;
* behaviour in Chrome on Windows (only Chromium on Linux);
* SmartScreen or antivirus prompts;
* a corporate proxy during `pip install`;
* human usability.

The step-by-step procedure to close these is in `docs/WINDOWS_LAPTOP_VERIFICATION.md`.
