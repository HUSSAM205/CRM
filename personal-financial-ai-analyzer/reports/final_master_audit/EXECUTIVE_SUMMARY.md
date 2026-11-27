> **Superseded (2026-11-27, master audit 2)** by [`FINAL_MASTER_AUDIT.md`](FINAL_MASTER_AUDIT.md). Kept unchanged below as the record of the first master audit.

# Executive Summary: Personal Financial AI Analyzer & Advisor (master audit)

**Final status: READY WITH DOCUMENTED LIMITATIONS.** The open items are:
* Windows execution is NOT TESTED;
* HW1 P5 is PARTIAL (the target laptop was not measured);
* forecasting ML is REJECTED on this synthetic data, so a deterministic outlook is shown.

The audit does **not** claim a perfect AI model, and it gives no 100% score.

| # | Item | Result |
|---|---|---|
| 1 | Branch | `claude/hopeful-noether-t6vfi7` |
| 2 | Commits | code verified at `0952509` (fresh clone); reports-only commits after it (see `git log`) |
| 3 | Files changed since the baseline `2cca378` | 161 files at `0952509` (75 added, 78 modified, 6 renamed, 2 deleted). The final report commits add a few report files |
| 4 | Dataset identity | **VERIFIED**: `ziadatalabs/FreeFinancialTransactions50M` @ `98cf38f9…`, 1,594,749,644 B, SHA-256 `b18c8359…7c17` (re-hashed, equal to the official LFS oid) |
| 5 | Rows | 50,000,000 (9 columns, 1,000,000 accounts, 2024-01-01..2026-07-31); full audit, 0 rows lost |
| 6 | Financial reconciliation | **9,488/9,488 exact** (independent PyArrow vs production; currency × month, × category, records, accounts). Curated cases 100% exact. Defect M-02 (silent int64 total overflow) found and fixed |
| 7 | Forecasting | HW2 E2 unchanged: GBR kept by HW2's rule (validation MAE 26.554 vs MA3 42.507). **E2-QG gate:** GBR and extended GBR **REJECTED**, because zero is better (validation 24.697; test 25.374 vs GBR 27.194) on all 5 panels. Cause: no learnable signal (autocorrelation −0.044, \|ρ\| ≤ 0.133) and a shift in the zero share. Product: historical-median outlook, test MAE 26.546, with an 80% interval covering 81.9% of test cells |
| 8 | Anomaly detection | 1%, k = 241: AUC 0.56–0.59; F1 0.008 (per-account IF), 0.037 (z), 0.041 (global IF); FPR about 1%; amount anomalies AUC 0.80; hour and category at chance. Status PARTIAL: "Unusual transaction — review recommended.", never fraud |
| 9 | Analyzer | **PASS**: overview, period spending, statistics, recorded inflows, cash flow (not a balance), recurring candidates, behaviour changes, transparent indicators |
| 10 | Advisor | **PASS**: goals (required monthly, completion, milestones, feasibility), emergency fund, what-if (simulation), affordability (never confirmed without a balance), ranked recommendations with 12 evidence fields |
| 11 | Assistant | **PASS**: 13 deterministic intents, scope-validated, read-only, isolation-tested; out-of-scope topics refused |
| 12 | Security | **PASS**: 0 known vulnerabilities, 0 secrets, no network, uploads in memory, deletion and retention work, 0 IDs in logs; residual: no authentication |
| 13 | Performance | Cloud container: jobs ≤ 1.86 GB (4 GB guard); warm inference 0.4–20 ms; cold model load 1.2–1.5 s; first page render 0.12–1.5 s; server start 0.9 s. **The laptop was not measured** |
| 14 | Tests passed | **177** (development, with data); **173** (fresh clone, no data) |
| 15 | Tests failed | **0** |
| 16 | Tests skipped | **0** (development); **4** in the fresh clone, all data-dependent with stated reasons |
| 17 | Browser workflows | **21/21** (development and fresh clone; mean 2.36 s, max 5.9 s). An intermediate 8/21 exposed M-11, which was fixed |
| 18 | Fresh clone | `0952509` with `python3.12`: setup 24 s; 173 passed / 4 skipped; 7/7 artifacts load without the dataset (M-06 fixed); 21/21 browser; 0 tracebacks |
| 19 | Windows | **NOT TESTED** (scripts `setup/run/train/test/audit.bat` and `.ps1` provided; dependency resolution verified) |
| 20 | Academic compliance | HW1+HW2: **67 PASS, 1 PARTIAL (P5), 1 N/A (P3), 0 FAIL** of 69; all 9 functional requirements PASS; E2 frozen, enhancements separate. Product requirements: 38 / 1 / 1 of 40 |
| 21 | Remaining blockers | none technical; Windows run and laptop timing need the student's machine; commercial licence is a legal question |
| 22 | Start the app | `setup.bat` then `run.bat` (Windows), or `python3.12 scripts/setup_environment.py` and `.venv/bin/python scripts/run_application.py` |
| 23 | Reproduce training and evaluation | `train.bat` / `.venv/bin/python scripts/run_full_pipeline.py`; then `scripts/research/forecast_quality_gate.py`; read-only check `audit.bat` |
| 24 | Reports | this folder: the 23 required reports plus `BASELINE.md`, `KNOWN_ISSUES.md` and raw evidence (JSON, logs, `freshclone_final/`); earlier packages `reports/audit/` and `reports/final_audit/`; `docs/` |

**Previously reported vs newly reproduced:** the dataset identity, the reconciliation (extended from 54 to 9,488 checks), all E2 and E3 metrics (re-run, Δ = 0), fresh-clone installation and the browser workflows were **re-executed** in this audit. Earlier claims that were corrected: M-03 (an overstated bound in the final-audit report) and M-07 (earlier fresh clones ran on CPython 3.13).
