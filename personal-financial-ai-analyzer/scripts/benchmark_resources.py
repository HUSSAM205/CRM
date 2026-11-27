"""Representative resource benchmarks (read-only on the raw dataset).

Each benchmark runs in a FRESH subprocess so its peak RSS (ru_maxrss) is measured in isolation and
cannot be inflated by memory retained from a previous benchmark.

Benchmarks:
  B1 footer/metadata read
  B2 full-column projection scan (count + min/max)       - lazy, streaming
  B3 full group_by account (1M groups)                    - streaming
  B4 account-currency-month spending aggregate (full)     - streaming
  B5 pyarrow row-group batch iteration over all rows      - constant-memory batch path
  B6 repeated partition collects in ONE process (diagnoses RSS growth seen in the ledger script)
  B7 same as B6 but each partition in its own subprocess  (mitigation)
Outputs: reports/benchmarks/resource_benchmarks.json
"""
from __future__ import annotations

import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/transactions_50M.parquet"
OUT = ROOT / "reports/benchmarks"

BENCH = {
"B1_metadata": """
import pyarrow.parquet as pq
md = pq.ParquetFile(RAW).metadata; rows = md.num_rows
""",
"B2_projection_scan": """
import polars as pl
r = pl.scan_parquet(RAW).select(pl.len(), pl.col('amount').min().alias('amin'), pl.col('amount').max().alias('amax'),
    pl.col('transaction_timestamp').min()).collect(engine='streaming'); rows = 50_000_000
""",
"B3_groupby_account": """
import polars as pl
r = pl.scan_parquet(RAW).group_by('account_id').agg(pl.len(), pl.col('amount').sum()).collect(engine='streaming')
rows = 50_000_000
""",
"B4_account_currency_month": """
import polars as pl
r = (pl.scan_parquet(RAW).filter(pl.col('status')=='completed')
     .with_columns(pl.col('transaction_timestamp').str.slice(0,7).alias('month'),
                   (pl.col('amount')*100).round(0).cast(pl.Int64).alias('c'))
     .group_by('account_id','currency','month').agg(pl.col('c').sum()).collect(engine='streaming'))
rows = 50_000_000
""",
"B5_pyarrow_batches": """
import pyarrow.parquet as pq, pyarrow.compute as pc
pf = pq.ParquetFile(RAW); rows = 0; s = 0.0
for b in pf.iter_batches(batch_size=1_000_000, columns=['amount','status']):
    rows += b.num_rows; s += pc.sum(b.column('amount')).as_py()
""",
"B6_partitions_one_process": """
import polars as pl, psutil, gc
lf = pl.scan_parquet(RAW).with_columns(pl.col('account_id').str.slice(4).cast(pl.Int64).alias('n'))
trace = []
for p in range(6):
    df = lf.filter(pl.col('n') % 20 == p).collect(engine='streaming')
    d = df.sort('account_id','transaction_id'); del df, d; gc.collect()
    trace.append(round(psutil.Process().memory_info().rss/1e9, 2)); print('trace', trace, flush=True)
rows = 6 * 2_500_000; extra = {'rss_after_each_partition_gb': trace}
""",
}

B7_CHILD = """
import polars as pl
lf = pl.scan_parquet(RAW).with_columns(pl.col('account_id').str.slice(4).cast(pl.Int64).alias('n'))
df = lf.filter(pl.col('n') % 20 == P).collect(engine='streaming'); d = df.sort('account_id','transaction_id')
rows = df.height
"""

WRAP = """
import resource, time, json, sys
RAW = {raw!r}
P = {p}
t = time.time(); extra = {{}}
{body}
print(json.dumps({{'seconds': round(time.time()-t, 2), 'rows': rows,
  'peak_rss_gb': round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e6, 2), **extra}}))
"""


def run(body: str, p: int = 0) -> dict:
    """Run one benchmark in a memory-guarded child process (configs/resource_limits.yaml)."""
    sys.path.insert(0, str(ROOT))
    from src.utils.resource_monitor import run_guarded
    code = WRAP.format(raw=str(RAW), p=p, body=body)
    g = run_guarded([sys.executable, "-c", code], cwd=ROOT)
    guard = {"guard_peak_rss_gb": g.peak_rss_gb, "guard_min_system_available_gb": g.min_system_available_gb,
             "killed_reason": g.killed_reason}
    if not g.ok:
        return {"error": (g.killed_reason or g.stderr_tail[-1500:]), "partial_stdout": g.stdout_tail[-1500:], **guard}
    res = json.loads(g.stdout_tail.strip().splitlines()[-1])
    res.update(guard)
    if res.get("seconds"):
        res["rows_per_second"] = int(res["rows"] / res["seconds"])
    return res


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    import polars as pl
    import psutil
    results = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "host": {"platform": platform.platform(), "cpus_logical": os.cpu_count(),
                        "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 2),
                        "ram_available_gb_at_start": round(psutil.virtual_memory().available / 1e9, 2),
                        "polars": pl.__version__, "polars_threads": pl.thread_pool_size()},
               "benchmarks": {}}
    for name, body in BENCH.items():
        res = run(body)
        results["benchmarks"][name] = res
        print(name, res, flush=True)
    b7 = [run(B7_CHILD, p) for p in range(6)]
    results["benchmarks"]["B7_partitions_subprocess_each"] = {
        "per_partition": b7, "max_peak_rss_gb": max(x.get("peak_rss_gb", 0) for x in b7)}
    print("B7", results["benchmarks"]["B7_partitions_subprocess_each"], flush=True)
    (OUT / "resource_benchmarks.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
