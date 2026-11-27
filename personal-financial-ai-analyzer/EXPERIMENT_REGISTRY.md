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

## Master audit runs (2026-11-27)

| Run | Completed (UTC, output mtime) | Command | Outcome | Outputs |
|---|---|---|---|---|
| MA-01 | 05:56 | baseline `pytest` (psutil-monitored) | 125 passed, 10.2 s, 0.63 GB | `reports/final_master_audit/baseline_pytest.txt` |
| MA-02 | ~06:00 | `python scripts/audit/dataset_manifest.py` | SHA matches; 8/8 advertised properties; 27/27 integrity | `DATASET_MANIFEST.json`, `DATA_QUALITY_REPORT.json` |
| MA-03 | ~06:02 | `scripts/audit/reconcile_granular.py` (guarded) | 9,488 checks, 0 mismatches; 53.9 s; 0.90 GB | `financial_reconciliation.json`, `logs/execution/master_reconcile_granular.log` |
| MA-04 | 06:08 | `scripts/research/forecast_quality_gate.py` (guarded) | E2-QG: both GBR REJECTED on 5 panels; outlook = historical median; interval test coverage 81.9%; 198 s; 0.74 GB | `reports/experiments/forecasting_quality_gate/`, `artifacts/forecasting/outlook/v_20261127T060820Z` |
| MA-05 | — | `node scripts/ux/ux_tasks.mjs` | 21/21 | `reports/ux_tasks/ux_task_results.json` |
| MA-06 | — | `python scripts/audit/benchmark_master.py` | recorded | `reports/final_master_audit/performance_benchmarks.json` |

## Master audit 2 runs (2026-11-27)

| Run | Command | Outcome | Outputs |
|---|---|---|---|
| M2-01 | baseline pytest | 177 passed | `reports/final_master_audit/BASELINE_STATE.md` |
| M2-02 | Dataset B download (pinned `c90078ae`) and `scripts/download_supplementary.py` | 2 files, SHA-256 match | `data/supplementary/` (ignored) |
| M2-03 | `scripts/research/dataset_b_audit.py` (guarded) | 29,812,435 rows, 22,018 users; 3.5 s, 1.56 GB | `reports/experiments/dataset_b/quality.json` |
| M2-04 | `scripts/research/forecast_dataset_b.py` (guarded; 1st attempt crashed on a Polars literal, fixed) | E2-B ACCEPTED; 60.2 s, 0.60 GB | `reports/experiments/forecasting_dataset_b/`, `artifacts/forecasting/gbr_personaledger/v_20261127T113730Z` |
| M2-05 | `scripts/research/forecast_dataset_b_checks.py` | bootstrap CIs exclude 0; guard selects 0% of A | `checks.json` |
| M2-06 | `scripts/research/anomaly_dataset_b.py` (1st attempt: null labels found → unlabelled sequences excluded) | chance-level AUC | `reports/experiments/anomaly_dataset_b/` |
| M2-07 | `scripts/research/controlled_synthetic.py` (1st run exposed M-12 TRY rejection; 2nd run before M-14; 3rd after) | C1 exact; C2 P 0.986 / R 0.865; C3 positive control; C4 before/after | `reports/experiments/dataset_c/` |
| M2-08 | `node scripts/ux/ux_tasks.mjs` | 24/24 | `reports/ux_tasks/ux_task_results.json` |
| M2-09 | `scripts/audit/benchmark_master.py` | recorded | `reports/final_master_audit/performance_benchmarks.json` |

## Master audit 3 (verification and reproduction only; no training, no change to E1–E4 or their outputs)

| Run | Command | Outcome | Outputs |
|---|---|---|---|
| M3-01 | `python scripts/verify_dataset.py` | OVERALL PASS (50,000,000 rows, 9 columns, SHA-256 `b18c8359…7c17` = live HF LFS) | console |
| M3-02 | `python scripts/download_supplementary.py` (files present: hash check only) | PASS ×2; HF head revision is still `c90078ae…` | console |
| M3-03 | `python scripts/audit/reproduce_e2b.py` (read-only, saved artifact) | match = true: MAE 971.342 vs 1,022.657; coverage 0.77653 | `reports/master_audit_3/e2b_reproduction.json` |
| M3-04 | `python scripts/audit/anomaly_derived_metrics.py` (read-only, saved E3 scores) | P@k equals the saved value for all 3 models; F1/FPR derived | `reports/master_audit_3/anomaly_derived_metrics.json` |
| M3-05 | `python scripts/audit/benchmark_master.py --label "cloud container…"` | recorded (container, not the laptop) | `reports/master_audit_3/benchmark_container.json` |
| M3-06 | `node scripts/ux/ux_tasks.mjs http://localhost:8501` | 29/29 | `reports/ux_tasks/ux_task_results.json` |
| M3-07 | fresh copy of the tracked tree: `python3.12 scripts/setup_environment.py`, pytest, launcher | setup 34 s; 217 passed / 4 skipped; health ok | `reports/master_audit_3/fresh_install/` |
| M3-08 | `pip-audit -r requirements.txt` | No known vulnerabilities found | console |
