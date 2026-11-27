# Changelog

## 2026-11-27: Verification phase

* Dataset download (pinned HF commit `98cf38f9`), integrity verification (27 checks), identity verification against `resolve/main`.
* Ledger semantics investigation over all 50M rows (conclusive).
* Full-data audit, methodology feasibility checks, real-data financial cross-check.
* Memory-guarded partitioned execution (`src/utils/resource_monitor.py`); resource benchmarks.
* Rules core (`src/rules/`), validator (`src/data/validation.py`), financial metrics (`src/analytics/financial_metrics.py`), 27 unit tests.
* Academic analysis, traceability, conflicts, decisions, verification reports.
* 11 defects found and fixed (K-01…K-11).
