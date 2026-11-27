# Fresh Install Audit

The procedure was run four times, each time in a new clean directory:

1. `git clone` of the pushed branch.
2. `python scripts/setup_environment.py`, which creates a stdlib venv and installs the pinned requirements with pip.
3. `python -m pytest`.
4. `streamlit run app/main.py`.
5. The 15 real-browser tasks.

| Clone | Commit | Setup | Tests | App | UX | Status |
|---|---|---|---|---|---|---|
| 1 (before fix) | `157bf5d` | PASS | **10 collection errors**: `ModuleNotFoundError: No module named 'src.data'` | Crashed on the Transactions page (same import) | **0/15** (15 FAIL; the script then aborted) | **FAIL → defect A-08 (P0)** |
| 2 (after the A-08 fix) | `b64e65b` | PASS | 119 passed, 3 skipped, **1 failed**: L10 `FileNotFoundError` on the derived `anomaly_transactions.parquet` (wrong skip condition) | OK | 14/15 (task 7, budget edit, timed out) | FAIL → A-09 and A-10 |
| 3 (after all fixes) | `0da7bbb` | PASS | **120 passed, 4 skipped** (data-dependent, correctly skipped without the dataset) | Started, **0 tracebacks** | **15/15** | **PASS** |
| 4 (final delivered commit) | `ed4d45c` | PASS (26 s; **CPython 3.13**, see M-07) | **121 passed, 4 skipped, 0 failed** | Started, **0 tracebacks** | **15/15** | **PASS** |

Evidence:
* `freshclone_before_fix/` (pytest, app tail, UX output of clone 1);
* `freshclone2_partial_fix/`, `freshclone4_final/` (same file set);
* `freshclone3_after_fix/` (`setup_tail.txt`, `pytest.txt`, `app_log.txt` with network URLs removed, `ux_results.txt`, `commit.txt`).

## Root cause of A-08

The parent CRM repository's `.gitignore` contains `data/` and `*.log`. Those patterns silently excluded `src/data/`, `data/samples/`, `data/external/` and every evidence log from git. Development worked only because the files existed locally, so the earlier "27/27 PASS" acceptance never exercised a clean checkout.

**Fix:** re-include rules in the project `.gitignore`, plus the regression test `tests/regression/test_repository_completeness.py`. That test asserts every source, config, fixture, sample and artifact file is tracked, and that no dataset or venv file is tracked.

## Not tested

* **Windows install (`setup.bat` / `setup.ps1`): NOT TESTED.** No Windows host is available. Only dependency resolution for win_amd64 / CPython 3.12 was verified (`reports/verification/requirements-windows-resolved.txt`).
* **The user's physical laptop: NOT TESTED.**
* The full data pipeline from a fresh clone (download 1.6 GB, then rebuild) was not re-run end to end. Its components were re-run in this audit: the dataset was verified, a partition resume was rerun, and training was re-executed.
