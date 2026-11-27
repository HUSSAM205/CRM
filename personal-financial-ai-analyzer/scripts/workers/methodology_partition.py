"""Worker: read-only methodology feasibility counts for ONE account partition.

Definitions (docs/experimental_design.md):
  spending record  = completed debit / withdrawal / fee  (refunds reduce the monthly target but do
                     not make a month "active")
  active month     = calendar month with >= 1 spending record for that account AND currency
  eligibility      = >= 12 active months inside the TRAINING period only (2024-01..2025-12),
                     so no validation/test information is used to select series (no leakage)
usage: methodology_partition.py <part> <n_parts> <checkpoint_dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/transactions_50M.parquet"
TRAIN = ("2024-01", "2025-12")
VAL = ("2026-01", "2026-04")
TEST = ("2026-05", "2026-07")


def period(m: pl.Expr) -> pl.Expr:
    return (pl.when(m <= TRAIN[1]).then(pl.lit("train"))
              .when(m <= VAL[1]).then(pl.lit("val")).otherwise(pl.lit("test")))


def main() -> None:
    part, n_parts, ck = int(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
    df = (pl.scan_parquet(RAW)
            .filter(pl.col("account_id").str.slice(4).cast(pl.Int64) % n_parts == part)
            .filter(pl.col("status") == "completed")
            .select("account_id", "currency", "transaction_type",
                    pl.col("transaction_timestamp").str.slice(0, 7).alias("month"))
            .with_columns(period(pl.col("month")).alias("period"))
            .collect(engine="streaming"))
    spend = df.filter(pl.col("transaction_type").is_in(["debit", "withdrawal", "fee"]))
    series = (spend.group_by("account_id", "currency")
                   .agg(pl.col("month").filter(pl.col("period") == "train").n_unique().alias("train_active"),
                        pl.col("month").filter(pl.col("period") == "val").n_unique().alias("val_active"),
                        pl.col("month").filter(pl.col("period") == "test").n_unique().alias("test_active"),
                        (pl.col("period") == "test").sum().alias("test_spend_records")))
    series.write_parquet(ck / f"part_{part:03d}.parquet")
    (ck / f"part_{part:03d}.json").write_text(json.dumps({"partition": part, "series": series.height}))


if __name__ == "__main__":
    main()
