# Resource Budget (16 GB laptop)

`configs/resource_limits.yaml`: worker hard limit 4.0 GB, soft target 3.0 GB, system-available floor 3.0 GB, 50 account partitions, 4 Polars threads, one worker at a time. It is enforced by `src/utils/resource_monitor.py`, which runs each heavy job as a child process, samples RSS and system memory every 0.25 s, kills on a breach, and checkpoints for resume.

Measured peaks:

| Job | Peak RSS |
|---|---|
| Ledger worker | 0.81 GB |
| Audit steps | ≤ 1.02 GB |
| Aggregation worker | 1.19 GB |
| Forecasting run | 1.35 GB (main process plus 4 ETS workers) |
| Anomaly run | 1.44 GB |

Two prohibited patterns were caught by the guard:

* unpartitioned full aggregation: more than 4 GB;
* single-process partition loop: 12.1 GB.
