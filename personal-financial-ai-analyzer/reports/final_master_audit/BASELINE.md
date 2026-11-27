# Baseline before the master audit (Phase 0)

Recorded 2026-11-27 05:55 UTC, before any change in this phase.

## Git state

| Item | Value |
|---|---|
| Directory | `/home/user/CRM/personal-financial-ai-analyzer` (a project folder inside the `HUSSAM205/CRM` repository) |
| Branch | `claude/hopeful-noether-t6vfi7` |
| HEAD | `2cca3784e4dcd04e869e2b031f8c875effb217c0` (equal to the remote branch) |
| Working tree | clean: 0 modified, 0 staged, 0 untracked |
| Checkpoint tag | `master-audit-start-20261127T055548Z` (local, at HEAD). Earlier tag: `audit-start-20261127T041513Z` |
| Ignore rules | Parent `.gitignore` (`data/`, `*.log`, node) plus the project `.gitignore`, which re-includes `src/data/`, `data/` and `*.log`, and ignores `data/raw/*.parquet`, `data/interim/`, `data/processed/`, `.venv/`, `.env` and checkpoint parquet. Guarded by `tests/regression/test_repository_completeness.py` |

## Tests, application and models

| Check | Result | Evidence |
|---|---|---|
| Test suite (with the dataset and derived data present) | **125 passed, 0 failed, 0 skipped**; 10.2 s wall; peak RSS 0.632 GB (process tree, psutil) | `baseline_pytest.txt` |
| Model artifacts | 6/6 load in a fresh process (`verify_artifacts.py`) | console output |
| App server start (`/_stcore/health` = ok) | cold 0.92 s, warm 0.72 s | measured by the audit script |
| Browser workflow (last run, before this phase) | 15/15 (`reports/ux_tasks/ux_task_results.json`, 05:17 UTC) | earlier run; re-run at the end of this phase |
| Fresh clone (last run) | `ed4d45c`: 121 passed, 4 skipped, UX 15/15 | `reports/audit/freshclone4_final/` |

**Product scope at baseline:** the Analyzer (6 pages), forecasting, anomaly review and a 5-intent assistant. There was **no Advisor pillar**: no goals, savings plans, scenarios, affordability checks or ranked recommendations, and no Settings page. Closing that gap is the main work of this phase.
