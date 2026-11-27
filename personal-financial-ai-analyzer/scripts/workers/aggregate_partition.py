"""Worker (Gate 4): validate one account partition and write its derived tables.

usage: aggregate_partition.py <part> <n_parts> <checkpoint_dir>
Outputs (one file per partition; directories from configs/preprocessing.yaml):
  monthly/part_XXX.parquet           account x currency x month summary (src.analytics.financial_metrics)
  monthly_category/part_XXX.parquet  account x currency x month x category net spending
  series_stats/part_XXX.parquet      per account-currency active spending months per split period
  rejected/part_XXX.parquet          every rejected row with its reason (may be empty)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.utils.peak_memory import peak_rss_gb  # noqa: E402
from src.data.preprocessing import process_partition  # noqa: E402
from src.utils.configuration import load_config  # noqa: E402

RAW = ROOT / "data/raw/transactions_50M.parquet"


def main() -> None:
    part, n_parts, ck = int(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
    t0 = time.time()
    out = {k: ROOT / v for k, v in load_config("preprocessing")["outputs"].items()}
    for d in out.values():
        d.mkdir(parents=True, exist_ok=True)
    raw = (pl.scan_parquet(RAW)
             .filter(pl.col("account_id").str.slice(4).cast(pl.Int64) % n_parts == part)
             .collect(engine="streaming"))
    out_p = process_partition(raw)
    res, ms, stats = out_p.validation, out_p.monthly, out_p.series_stats
    name = f"part_{part:03d}.parquet"
    res.rejected.write_parquet(out["rejected_dir"] / name)
    ms.write_parquet(out["monthly_dir"] / name)
    out_p.category.write_parquet(out["monthly_category_dir"] / name)
    stats.write_parquet(out["series_stats_dir"] / name)
    (ck / f"part_{part:03d}.json").write_text(json.dumps({
        "partition": part, "rows": raw.height, "clean": res.clean.height, "rejected": res.rejected.height,
        "reject_reasons": res.reason_counts,
        "unresolved_type_rows": int((res.clean["meaning"] == "unresolved").sum()),
        "monthly_rows": ms.height, "series": stats.height,
        "worker_seconds": round(time.time() - t0, 2),
        "worker_ru_maxrss_gb": peak_rss_gb()}), encoding="utf-8")


if __name__ == "__main__":
    main()
