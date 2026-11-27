"""Worker: transaction_id structure/uniqueness for ONE id partition.

Partition key = numeric part of transaction_id modulo n_parts. Two equal ids always have the same
numeric part, so they always fall in the same partition: per-partition uniqueness counts sum to the
exact global counts (a single global n_unique over 50M strings exceeded the 4 GB worker limit).
usage: id_partition.py <part> <n_parts> <checkpoint_dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.utils.peak_memory import peak_rss_gb  # noqa: E402
RAW = ROOT / "data/raw/transactions_50M.parquet"


def main() -> None:
    part, n_parts, ck = int(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
    num = pl.col("transaction_id").str.slice(2, 10).cast(pl.Int64)
    r = (pl.scan_parquet(RAW).select("transaction_id")
           .filter(num % n_parts == part)
           .select(pl.len().alias("rows"),
                   pl.col("transaction_id").str.contains(r"^TX\d{10}$").sum().alias("ids_TX_plus_10_digits"),
                   pl.col("transaction_id").str.contains(r"^TX\d{10}-zdl26nr51f60aaa959f$").sum()
                     .alias("ids_with_suffix"),
                   pl.col("transaction_id").n_unique().alias("unique_ids"),
                   num.n_unique().alias("unique_numeric_parts"),
                   num.min().alias("min_numeric"), num.max().alias("max_numeric"))
           .collect(engine="streaming").to_dicts()[0])
    r["worker_ru_maxrss_gb"] = peak_rss_gb()
    (ck / f"part_{part:03d}.json").write_text(json.dumps(r), encoding="utf-8")


if __name__ == "__main__":
    main()
