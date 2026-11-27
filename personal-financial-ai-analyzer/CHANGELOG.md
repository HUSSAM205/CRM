# Changelog

## 2026-11-27: Verification phase

* Dataset download (pinned HF commit `98cf38f9`), integrity verification (27 checks), identity verification against `resolve/main`.
* Ledger semantics investigation over all 50M rows (conclusive).
* Full-data audit, methodology feasibility checks, real-data financial cross-check.
* Memory-guarded partitioned execution (`src/utils/resource_monitor.py`); resource benchmarks.
* Rules core (`src/rules/`), validator (`src/data/validation.py`), financial metrics (`src/analytics/financial_metrics.py`), 27 unit tests.
* Academic analysis, traceability, conflicts, decisions, verification reports.
* 11 defects found and fixed (K-01…K-11).

## 2026-11-27: Implementation phase (Gates 4–16)

* Partitioned preprocessing of all 50M rows; HW2 splits; forecasting (baselines, ETS, GBR) and anomaly (robust z, per-account and global IF) experiments with robustness runs, diagnostics and a positive control.
* Versioned artifacts with a registry; fresh-process verification.
* Streamlit app (6 sections), deterministic assistant, budgets, privacy controls, CSV export.
* 118 automated tests; 12/12 real-browser user tasks; figures; final evidence; documentation.
* Defects K-12…K-21 found and fixed with regression tests.

## 2026-11-27: Independent final audit

* Re-verified the dataset identity live (unchanged before and after); full-scale independent reconciliation (54/54); resume and determinism (9/9); training re-executed from scratch with every metric reproduced (Δ = 0.0); full-population forecasting check.
* Fixed:
  * A-08 (P0): fresh clone broken by the parent `.gitignore`;
  * A-01 (P1): overflow crash in the validator;
  * A-02: missing date filter (HW1 S7);
  * A-03: Markdown injection;
  * A-04: telemetry and tracebacks;
  * A-05: ISO `T` timestamps;
  * A-06: deprecated API;
  * A-09: leakage-test skip condition;
  * A-10: flaky browser step.
* New tests: repository completeness, overflow, date filter, saved-budget flow, ISO timestamps. Three extra browser tasks (15 in total).
* Corrected the overstated "27/27 PASS" and the S7/P1 traceability rows. Added `reports/audit/` and `reports/final_audit/`.

## 2026-11-27: Master audit: Analyzer & Advisor

* **Advisor pillar** (`src/advisor/`, Financial advisor page): context of known/unknown facts, savings goals, emergency fund, what-if scenarios, affordability (never confirmed without a balance), ranked evidence-based recommendations.
* **Analyzer extensions** (`src/analytics/insights.py`, Analytics tabs, Overview): period spending, statistics, recorded inflows, cash flow, recurring candidates, behaviour changes, transparent indicators.
* **Forecasting quality gate E2-QG**: zero/median baselines, extended GBR, diagnostics, calibrated interval; GBR REJECTED; product shows the deterministic outlook (D-22).
* **Assistant**: 13 deterministic intents, scope validation, read-only; out-of-scope topics refused.
* Anomaly alerts with full evidence and "Unusual transaction — review recommended.".
* Settings and privacy page; goals and facts purged on delete.
* Fixed M-01..M-05 (incl. silent int64 total overflow M-02). Security regression tests. `audit.bat`/`audit.ps1`.
* Docs renamed to avoid case collisions on Windows; new ANALYZER, ADVISOR, FORECASTING, ANOMALY_DETECTION, AI_ASSISTANT, SECURITY_AND_PRIVACY, MODEL_CARD, WINDOWS_INSTALLATION docs.
* Evidence package `reports/final_master_audit/`.
