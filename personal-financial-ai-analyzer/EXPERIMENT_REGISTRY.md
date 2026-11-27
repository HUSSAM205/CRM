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

## Model experiments

None yet.
