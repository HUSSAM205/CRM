# Resource Benchmark Report

Generated 2026-11-27 04:06 UTC from `reports/benchmarks/resource_benchmarks.json`, `ledger_semantics.json` and `data_audit/dataset_overview.json`.

## Host (measured: the cloud execution container, NOT the user's laptop)
`{'platform': 'Linux-6.18.44-fc-v880-x86_64-with-glibc2.39', 'cpus_logical': 4, 'ram_total_gb': 16.87, 'ram_available_gb_at_start': 15.14, 'polars': '2.2.0', 'polars_threads': 4}`

User laptop (user-reported, **not measurable from here**): Intel i7-1355U (10 cores / 12 threads), 16 GB DDR4-3200, Intel Iris Xe, no NVIDIA GPU, Windows 64-bit, about 350 GB free.

## Benchmarks (each in a guarded child process; limits in `configs/resource_limits.yaml`)
| Benchmark | Rows | Seconds | Rows/s | Peak RSS GB | Outcome |
|---|---|---|---|---|---|
| B1_metadata | 50000000 | 0.11 | 454545454 | 0.002 | ok |
| B2_projection_scan | 50000000 | 0.72 | 69444444 | 0.467 | ok |
| B3_groupby_account | 50000000 | 2.14 | 23364485 | 2.847 | ok |
| B4_account_currency_month | — | — | — | 4.141 | worker RSS 4.14 GB > hard limit 4.0 GB |
| B5_pyarrow_batches | 50000000 | 1.75 | 28571428 | 0.326 | ok |
| B6_partitions_one_process | 15000000 | 14.94 | 1004016 | 3.261 | ok |
| B7_partitions_subprocess_each | 6 × 2.5M | — | — | max 3.23 | ok |

## Production-pattern measurements
| Job | Pattern | Max worker peak RSS | Min system available |
|---|---|---|---|
| Ledger investigation (50 partitions) | one partition per child | 0.807 GB | 14.8 GB |
| ID uniqueness (50 ID partitions) | one partition per child | 0.251 GB | — |
| Audit global steps | one step per child | {'missing': 'checkpointed', 'distributions': 'checkpointed', 'calendar': 'checkpointed', 'amounts': 'checkpointed'} | — |
| Audit partitions | one partition per child | 0.869 GB | — |

## Conclusions
1. Unpartitioned full-data aggregations (B4) exceed the 4 GB worker budget, and single-process partition loops can
   retain memory (12.1 GB observed before the fix). **These patterns are prohibited** for this project.
2. Account-partitioned workers with 50 partitions (about 1M rows) peak below 1.1 GB, with about 3 s per partition here.
   On a 16 GB laptop this leaves a large margin, even with 6–8 GB used by Windows and applications.
3. Throughput is high (column-projected scans of 23–69M rows/s), so **Google Colab is not needed**: no measured
   limitation justifies it (`docs/local_vs_colab_benchmark.md`).
4. Laptop timings will differ (different CPU and OS) and were **not measured**. The memory pattern is the same
   because it depends on partition size, not on the host.
