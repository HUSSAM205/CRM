# Experiment Registry

Every run that produces numbers is listed here with its command, time and outputs. Nothing is omitted, including failures.

## Verification runs (no model training)

| Run | Completed (UTC, from output-file mtime) | Command | Outcome | Outputs |
|---|---|---|---|---|
| V-01 | 02:40:05 | `python scripts/download_dataset.py` | PASS (1st curl attempt failed, K-01) | `data/raw/PROVENANCE.json` |
| V-02 | 02:44:28 | `python scripts/verify_dataset.py` | PASS 27/27 | `reports/verification/dataset_integrity.json` |
| V-03 | ~02:50 (log only) | single-process ledger investigation | FAILED / killed: RSS 12.1 GB, global step incomplete (K-05) | superseded |
| V-04 | 02:57:18 | `python scripts/investigate_ledger.py` (guarded, 50 partitions) | PASS (the first attempt's global step was killed at 4.16 GB, K-06) | `ledger_semantics.json` |
| V-05 | 03:01:38 | `python scripts/run_audit.py` | PASS after K-07 and K-08 (two guard kills) | `reports/data_audit/` |
| V-06 | 02:49:08 | identity check against `resolve/main` | DATASET IDENTITY VERIFIED | `dataset_identity_check.txt` |
| V-07 | 03:03:50 | `python scripts/verify_methodology.py` | PASS M1–M5 | `methodology_feasibility.json` |
| V-08 | 03:07:38 / 03:10:50 | real-data cross-check, partitions 7 and 33 | PASS, 0 mismatches | `crosscheck_partition_*.json` |
| V-09 | 03:12:34 | `python scripts/benchmark_resources.py` | B4 killed at 4.14 GB (expected evidence); others ok | `reports/benchmarks/resource_benchmarks.json` |

## Pipeline and model runs

| Run | Completed (UTC) | Command | Outcome | Outputs |
|---|---|---|---|---|
| P-01 | 03:22:43 | `scripts/build_aggregates.py` | PASS: 50M rows, 0 rejected, peak 1.19 GB | `reports/data_audit/preprocessing_summary.json` |
| P-02 | 03:23:11 | `scripts/create_splits.py` | PASS: 106,945 eligible; 4 panels of 20k; 10k anomaly accounts | `data/processed/splits/split_metadata.json` |
| M-01 | 03:32:18 | `scripts/train_forecasting.py` (guarded) | PASS: 529 s, peak 1.35 GB; selected `gbr` | `reports/experiments/forecasting/`, `artifacts/forecasting/*/v_20261127T033218Z_*` |
| M-02 | between 03:32 and 03:38 (log overwritten by M-03) | `scripts/train_anomaly.py` | **FAILED** (K-14 injection crash, 3 s); no outputs | log overwritten by M-03; defect recorded |
| M-03 | 03:38:06 | `scripts/train_anomaly.py` (guarded) | PASS: 241 s, peak 1.44 GB | `reports/experiments/anomaly/`, `artifacts/anomaly/*/v_20261127T033806Z_*` |
| D-01 | 03:33:55 | `scripts/evaluate_models.py` + autocorrelation check | Diagnostic: zero forecast beats GBR | `reports/evaluation/forecasting_error_analysis.json` |
| D-02 | 03:38:55 | anomaly positive control | PASS: ×1000 AUC 0.999 | `reports/evaluation/anomaly_positive_control.json` |
| U-01 | 03:58:28 (final run) | `scripts/ux/ux_tasks.mjs` (Playwright, 7 iterations while fixing script and app defects) | Final: 12/12 | `reports/ux_tasks/ux_task_results.json` |

## Final audit runs (2026-11-27, no change to frozen experiments)

| Run | Completed (UTC) | Command | Outcome | Outputs |
|---|---|---|---|---|
| AU-01 | 04:15 | `python scripts/verify_dataset.py` plus live `curl -I` | PASS 27/27; identity unchanged | `logs/execution/audit_verify_dataset.log`, `reports/audit/dataset_identity_audit.md` |
| AU-02 | 04:17 | `python scripts/audit/reconcile_totals.py` | 54/54 exact | `reports/audit/reconciliation.json` |
| AU-03 | 04:18 | Delete 3 partitions, then `scripts/build_aggregates.py` (resume) | Only those 3 reran; 9/9 content-identical (after A-07) | `logs/execution/audit_resume_build_aggregates.log` |
| AU-04 | 04:27 | `python scripts/audit/training_audit.py` (guarded) | PASS: 472.7 s, peak 1.859 GB; Δ = 0.0 for all metrics; full-population check | `reports/audit/training_audit.json`, `logs/execution/audit_training.log` |
| AU-05 | 04:36 | Inference and latency micro-benchmarks | Recorded | `reports/audit/inference_performance.json` |
| AU-06 | 05:17:21 | `node scripts/ux/ux_tasks.mjs` | 15/15 | `reports/ux_tasks/ux_task_results.json` |
| AU-07 | 05:29:33 | `python scripts/run_all_tests.py` | 124 passed | `logs/testing/pytest_20261127T052933Z.log` |
| AU-08 | — | Fresh clones 1, 2 and 3 | 1: FAIL (A-08); 2: FAIL (A-09, A-10); 3: PASS (120 passed, 4 skipped, UX 15/15) | `reports/audit/freshclone*/` |
| AU-11 | — | Fresh clone 4 of `ed4d45c` | PASS: setup 26 s; 121 passed, 4 skipped; UX 15/15 | `reports/audit/freshclone4_final/` |
| AU-09 | 05:33 | `pip-audit`; static scans | 0 vulnerabilities, 0 secrets | `reports/audit/pip_audit.txt`, `static_security_scan.txt` |
| AU-10 | 05:29 | `python scripts/verify_artifacts.py` | Exit 0 | `logs/execution/audit_verify_artifacts.log` |

Completion times are output-file mtimes (UTC). A final test run after the report edits is recorded in `reports/final_audit/FINAL_TEST_RESULTS.md`.
