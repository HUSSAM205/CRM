# Baseline State (start of master audit 2)

Recorded 2026-11-27 11:31 UTC, before any change in this programme. Every value below was re-measured now, not copied from earlier reports.

| Item | Value | How verified |
|---|---|---|
| Branch / HEAD | `claude/hopeful-noether-t6vfi7` @ `40f366c4034d91024b3599663f9d789560c4f2b4` | `git rev-parse`; equal to `origin/…` after fetch |
| Working tree | clean (0 changes, 0 untracked) | `git status` |
| Checkpoint tag | `master2-start-20261127T113107Z` (local; earlier tags `audit-start-…`, `master-audit-start-…`) | `git tag` |
| Python | 3.12.3 (`.venv`) | `.venv/bin/python --version` |
| Dataset A identity | `transactions_50M.parquet`, SHA-256 `b18c83595d2e7a06598c00a3cbe01eb0586b2f0b10443305c6283586c27f8c17` (unchanged) | `sha256sum` |
| Model artifacts | forecasting: gbr, gbr_seasonal, selection, outlook; anomaly: isolation_forest_global, robust_zscore, isolation_forest_per_account (registry `artifacts/metadata/model_registry.json`) | `ls artifacts` |
| Tests | **177 passed, 0 failed, 0 skipped** (44 s on a loaded container) | `pytest` |
| Browser tasks | 21/21 (last run 06:48 UTC; re-run at the end of this programme) | `reports/ux_tasks/ux_task_results.json` |
| Academic traceability | 67 PASS / 1 PARTIAL (P5) / 1 N/A (P3) of 69 | `project_inventory.py` |
| Forecasting | E2 (HW2) GBR kept by the HW2 rule; E2-QG: GBR REJECTED (zero is better); product = deterministic outlook | `FORECASTING_EXPERIMENTS.md` |
| Anomaly | weak: F1@k 0.008–0.041, AUC 0.56–0.59 | `ANOMALY_EXPERIMENTS.md` |
| Application | 8 pages: Overview, Transactions, Analytics, AI predictions, Budget, Financial advisor, Financial assistant, Settings | `app/main.py` |
| Open items | Windows NOT TESTED; HW1 P5 PARTIAL; commercial licence BLOCKED; forecasting ML REJECTED | `KNOWN_ISSUES.md` |
| Unresolved defects | none known at start | `DEFECT_REGISTER.md` |

## Gaps against the new programme, found by inspecting the code

* **Advisor:**
  * no financial profile with essential vs non-essential expenses;
  * emergency fund has a fixed coverage of 3 months and no current emergency savings or progress;
  * savings goals cannot be **edited**, and have no status;
  * scenarios lack income increase, general expense change, one-off unexpected expense and goal impact;
  * recommendations lack an explicit "missing information" field.
* **Assistant:**
  * no "this month / last month", largest category, highest months, recurring-payment, remaining-budget or model-reliability questions;
  * no clarification for ambiguous input, and no refusal when another account is named;
  * the UI does not show the period, account or currency context of each answer.
* **Budget:** remaining budget is not shown.
* **Anomaly:** explanation reasons are not mapped to the standard labels (unusual amount, unusual timing, rare category, insufficient historical context); no per-account results.
* **Forecast output:** lacks explicit historical window, coverage, metrics and status fields.
* **Data:**
  * no dataset registry or licence register;
  * no supplementary-dataset research;
  * no controlled synthetic datasets with ground truth for forecasting and recurrence (Dataset C).
* **Performance:** no benchmark procedure for the student's laptop.
