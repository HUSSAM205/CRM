"""Worker: ledger checks for ONE account partition (run by scripts/investigate_ledger.py).

usage: ledger_partition.py <part> <n_parts> <checkpoint_dir>
Writes <checkpoint_dir>/part_XXX.json with aggregated counts only (no raw transaction values).
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
from src.rules.transaction_mapping import BALANCE_DIRECTION  # noqa: E402

RAW = ROOT / "data/raw/transactions_50M.parquet"


def with_deltas(df: pl.DataFrame, order: list[str]) -> pl.DataFrame:
    prev = pl.col("bal_c").shift(1).over("account_id")
    return (df.sort(["account_id", *order])
              .with_columns((pl.col("bal_c") - prev).alias("delta"), prev.is_null().alias("first"),
                            pl.when(pl.col("status") == "completed")
                              .then(pl.col("transaction_type").replace_strict(BALANCE_DIRECTION,
                                                                              return_dtype=pl.Int64)
                                    * pl.col("amt_c"))
                              .otherwise(0).alias("expected")))


def per_type(df: pl.DataFrame) -> list[dict]:
    return (df.filter(~pl.col("first")).group_by("transaction_type", "status")
              .agg(pl.len().alias("n"), (pl.col("delta") == pl.col("expected")).sum().alias("match"))
              .sort("transaction_type", "status").to_dicts())


def main() -> None:
    part, n_parts, ck = int(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
    t0 = time.time()
    df = (pl.scan_parquet(RAW)
            .filter(pl.col("account_id").str.slice(4).cast(pl.Int64) % n_parts == part)
            .select(pl.col("transaction_id").str.slice(2, 10).cast(pl.Int64).alias("seq"),
                    "account_id", "transaction_type", "status", "currency", "transaction_timestamp",
                    (pl.col("amount") * 100).round(0).cast(pl.Int64).alias("amt_c"),
                    (pl.col("balance_after") * 100).round(0).cast(pl.Int64).alias("bal_c"))
            .collect(engine="streaming"))
    a = with_deltas(df, ["seq"])
    b = with_deltas(df, ["transaction_timestamp", "seq"])
    acc = (a.group_by("account_id").agg(
               (~pl.col("first") & (pl.col("delta") != pl.col("expected"))).sum().alias("id_mismatch"),
               (pl.col("bal_c") < 0).any().alias("neg_balance"),
               pl.col("currency").n_unique().alias("currencies"),
               # timestamps are fixed-width strings, so string order == time order
               (pl.col("transaction_timestamp") < pl.col("transaction_timestamp").shift(1)).sum()
                 .alias("ts_inversions_in_id_order"))
             .join(b.filter(~pl.col("first")).group_by("account_id")
                    .agg((pl.col("delta") != pl.col("expected")).sum().alias("ts_mismatch")),
                   on="account_id", how="left"))
    out = {
        "partition": part, "rows": df.height, "accounts": acc.height,
        "per_type_by_id": per_type(a), "per_type_by_timestamp": per_type(b),
        "accounts_fully_reconciled_by_id": int((acc["id_mismatch"] == 0).sum()),
        "accounts_fully_reconciled_by_timestamp": int((acc["ts_mismatch"].fill_null(0) == 0).sum()),
        "accounts_id_order_equals_time_order": int((acc["ts_inversions_in_id_order"] == 0).sum()),
        "accounts_with_negative_balance": int(acc["neg_balance"].sum()),
        "accounts_multi_currency_single_balance": int((acc["currencies"] > 1).sum()),
        "worker_seconds": round(time.time() - t0, 2),
        "worker_ru_maxrss_gb": peak_rss_gb(),
    }
    (ck / f"part_{part:03d}.json").write_text(json.dumps(out), encoding="utf-8")


if __name__ == "__main__":
    main()
