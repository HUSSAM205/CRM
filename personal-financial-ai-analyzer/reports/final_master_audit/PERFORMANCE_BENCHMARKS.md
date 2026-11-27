# Performance Benchmarks

**Hardware:** cloud container, x86_64 Linux, CPython 3.12.3, 4 logical CPUs, 16.9 GB RAM. **This is not the target laptop** (Windows, i7-1355U, 16 GB, Iris Xe), which was not available. CPU-only; no GPU used.

Raw data: `performance_benchmarks.json`, from `python scripts/audit/benchmark_master.py`. Timing modes:
* **Cold:** the first call in a new Python process, including model loading. The OS file cache was not cleared.
* **Warm:** the median of 20 repeated calls.

Inference and training are reported separately, never summed.

## Application paths (demo data unless stated)

| Operation | Input | Cold first call | Warm median | CPU (warm) | Peak RSS |
|---|---|---|---|---|---|
| CSV ingest + validate | 195 rows | 15.0 ms | 7.1 ms | 122% | 0.08 GB |
| CSV ingest + validate | 200,000 rows | 481 ms | 426 ms | 122% | 0.30 GB |
| Build summaries | 195 rows | 5.4 ms | 4.4 ms | 150% | 0.08 GB |
| Forecast outlook (product) | 1 series | 10.7 ms | 0.41 ms | — | 0.10 GB |
| GBR load + forecast (academic) | 1 series | **1,454 ms** (model load) | 1.5 ms | — | 0.25 GB |
| IF load + unusual-transaction review | 1 account | **1,186 ms** (model load) | 14.4 ms | 120% | 0.26 GB |
| Assistant, HW2 intent | 1 question | 6.0 ms | 0.9 ms | — | 0.10 GB |
| Assistant, advisor intent | 1 question | 21.4 ms | 19.9 ms | 174% | 0.10 GB |
| Advisor recommendations | 1 account | 20.3 ms | 18.5 ms | 190% | 0.10 GB |
| Analyzer insights (indicators, behaviour, income) | 1 account | 19.9 ms | 20.3 ms | 173% | 0.10 GB |
| Dataset metadata (Parquet footer) | 1.59 GB file | 2.1 ms | 0.45 ms | — | 0.10 GB |

"—" means a tiny CPU-time quotient that is not meaningful.

**Page script execution (AppTest, server side, demo data, without browser paint):**

| Page | First render | Median re-render |
|---|---|---|
| Overview | 0.67 s | 0.21 s |
| Transactions | 0.12 s | 0.19 s |
| Analytics | 0.52 s | 0.22 s |
| AI predictions | 1.50 s (model load) | 0.18 s |
| Budget | 0.19 s | 0.19 s |
| Financial advisor | 0.24 s | 0.21 s |
| Financial assistant | 0.12 s | 0.17 s |
| Settings | 0.13 s | 0.12 s |

Peak 0.35 GB.

**App server start** (`/_stcore/health` = ok): 0.90 s cold, 0.79 s warm.

**Real-browser tasks:** see `BROWSER_TEST_RESULTS.md` for the measured mean and maximum per multi-step task.

## Offline pipeline (full 50M rows; each step run once, guarded)

| Step | Wall time | Peak RSS | Source |
|---|---|---|---|
| Dataset SHA-256 + footer | 6.5 s | — | `DATASET_MANIFEST.json` |
| Full audit, 50 partitions | 126 s of worker time (sum over partitions; max 0.87 GB per partition) | 0.87 GB | `logs/execution/audit_partitions.jsonl` |
| Aggregation, 50 partitions | about 3.6 s per partition | 1.19 GB per worker | `logs/preprocessing/aggregate_partitions.jsonl` |
| Granular reconciliation (independent) | 53.9 s | 0.90 GB | `logs/execution/master_reconcile_granular.log` |
| Forecasting E2 (original run, 4 panels) | 529 s | 1.35 GB | `logs/training/train_forecasting.log` |
| GBR E2, single fit (360k rows) | 1.4–1.5 s | — | `reports/audit/training_audit.json`, E2-QG |
| GBR extended, single fit | 5.6 s | — | E2-QG summary |
| Quality-gate experiment E2-QG, 5 panels | 198 s | 0.74 GB | `logs/training/forecast_quality_gate.log` |
| Anomaly E3 (9 runs) | 241 s | 1.44 GB | `logs/training/train_anomaly.log` |

**Memory bounds:** every heavy job ran in a child process under the 4 GB hard limit and 3 GB soft target. No job exceeded 1.86 GB, and system-available memory never fell below 12.7 GB. Unpartitioned attempts that exceeded 4 GB were killed by design (K-05..K-08).

**No retraining in the app:** the app only loads artifacts (`test_model_loading.py`, the static checks in `test_security.py`, and `inference.py`, which refuses ETS).
