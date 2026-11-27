# Performance and Resource Audit

All measurements are from the **cloud container** (x86_64 Linux, CPython 3.12.3). The user's 16 GB Windows laptop was **not measured**.

## Memory safety (the 16 GB laptop constraint)

| Workload | Peak RSS | Guard | Source |
|---|---|---|---|
| Preprocessing, 50 partitions (audit resume rerun) | 1.192 GB max worker | 4 GB hard / 3 GB soft | `logs/execution/audit_resume_build_aggregates.log` |
| Full data audit | ≤ 0.869 GB per partition | same | `logs/execution/run_audit.log` |
| Training-audit re-execution (all models plus the full population) | **1.859 GB**; system available ≥ 14.48 GB | same | `logs/execution/audit_training.log` |
| Original forecasting / anomaly training | 1.35 / 1.44 GB | same | `EXPERIMENT_REGISTRY.md` M-01, M-03 |
| App process after a full interaction set | 0.261 GB | — | `inference_performance.json` |

Unpartitioned operations that exceeded 4 GB were killed by the guard by design and are recorded (K-05..K-08, V-09 B4).

## Application latency (`inference_performance.json`, 20 runs each)

| Operation | Median | Max |
|---|---|---|
| Ingest and validate 195-row demo CSV | 6.1 ms | 9.1 ms |
| Build summaries | 4.2 ms | 4.9 ms |
| Forecast inference | 1.1 ms | 8.7 ms |
| Anomaly review candidates | 14.3 ms | 17.7 ms |
| Assistant answer | 0.9 ms | 2.3 ms |
| First model load (cold) | 1.31 s | — |
| Ingest a 200,000-row CSV | 0.5 s | — |
| Real-browser multi-step task (UX) | 2.40 s mean | 5.88 s |

HW1 P5 ("prompt response on final hardware") stays **PARTIAL**, because the final hardware was not available.
