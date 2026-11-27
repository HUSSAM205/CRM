"""Worker: per-account audit statistics for ONE account partition (run by scripts/run_audit.py).

usage: audit_partition.py <part> <n_parts> <checkpoint_dir>
Writes part_XXX.parquet (one row per account, aggregate statistics only) and part_XXX.json.
"""
from __future__ import annotations

import json
import resource
import sys
import time
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/transactions_50M.parquet"
SPEND = ["debit", "withdrawal", "fee"]
CONTENT_COLS = ["account_id", "transaction_type", "amount", "currency", "merchant_category",
                "balance_after", "transaction_timestamp", "status"]


def main() -> None:
    part, n_parts, ck = int(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
    t0 = time.time()
    df = (pl.scan_parquet(RAW)
            .filter(pl.col("account_id").str.slice(4).cast(pl.Int64) % n_parts == part)
            .with_columns(pl.col("transaction_timestamp").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S").alias("ts"))
            .collect(engine="streaming"))
    # Same content under different transaction_ids (reported, NOT removed: HW2 4.5(3))
    content_dups = df.height - df.select(CONTENT_COLS).n_unique()
    completed = pl.col("status") == "completed"
    month = pl.col("ts").dt.strftime("%Y-%m")
    acc = (df.sort("account_id", "ts")
             .group_by("account_id", maintain_order=True)
             .agg(pl.len().alias("n_tx"),
                  completed.sum().alias("n_completed"),
                  month.n_unique().alias("active_months_any"),
                  month.filter(completed & pl.col("transaction_type").is_in(SPEND)).n_unique()
                    .alias("active_spending_months"),
                  pl.col("currency").n_unique().alias("n_currencies"),
                  pl.col("merchant_category").n_unique().alias("n_categories"),
                  pl.col("ts").min().alias("first_ts"), pl.col("ts").max().alias("last_ts"),
                  (pl.col("ts").diff().dt.total_days().max()).alias("max_gap_days"),
                  (pl.col("balance_after") < 0).sum().alias("negative_balance_rows")))
    acc.write_parquet(ck / f"part_{part:03d}.parquet")
    (df.group_by(month.alias("month")).agg(pl.col("account_id").n_unique().alias("active_accounts"))
       .write_parquet(ck / f"part_{part:03d}.months.parquet"))
    (ck / f"part_{part:03d}.json").write_text(json.dumps({
        "partition": part, "rows": df.height, "accounts": acc.height,
        "same_content_different_id_rows": int(content_dups),
        "worker_seconds": round(time.time() - t0, 2),
        "worker_ru_maxrss_gb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 3)}))


if __name__ == "__main__":
    main()
