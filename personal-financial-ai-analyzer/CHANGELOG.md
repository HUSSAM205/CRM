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
