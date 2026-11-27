"""Ledger-semantics investigation over EVERY account (read-only).

Question: in what order, and with what sign, does balance_after change?
Method: for each account, order its records by a candidate key (transaction_id, or timestamp),
take delta = balance_after - previous balance_after in exact integer cents, and compare with the
hypothesis  delta == direction(type) * amount  for completed records and  delta == 0  otherwise.
The first record of each account has no predecessor and is counted separately.

Accounts are processed in 20 hash partitions (by numeric id mod 20) to bound memory.
Outputs: reports/verification/ledger_semantics.json (+ per-type CSV)
"""
from __future__ import annotations

import gc
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.rules.transaction_mapping import BALANCE_DIRECTION  # noqa: E402

RAW = ROOT / "data/raw/transactions_50M.parquet"
OUT = ROOT / "reports/verification"
PARTS = 20


def deltas(df: pl.DataFrame, order: list[str]) -> pl.DataFrame:
    return (df.sort(["account_id", *order])
              .with_columns(
                  (pl.col("bal_c") - pl.col("bal_c").shift(1).over("account_id")).alias("delta"),
                  pl.col("bal_c").shift(1).over("account_id").is_null().alias("first"))
              .with_columns(
                  pl.when(pl.col("status") == "completed")
                    .then(pl.col("transaction_type").replace_strict(BALANCE_DIRECTION, return_dtype=pl.Int64)
                          * pl.col("amt_c"))
                    .otherwise(0).alias("expected")))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    lf = pl.scan_parquet(RAW).with_columns(
        pl.col("account_id").str.slice(4).cast(pl.Int64).alias("acc_n"),
        (pl.col("amount") * 100).round(0).cast(pl.Int64).alias("amt_c"),
        (pl.col("balance_after") * 100).round(0).cast(pl.Int64).alias("bal_c"),
        # sequence key = the 10-digit numeric part; 200 ids carry an extra suffix (see report)
        pl.col("transaction_id").str.slice(2, 10).cast(pl.Int64).alias("seq"),
    )
    by_id_rows, by_ts_rows = [], []
    acct_stats = []
    peak = 0
    for p in range(PARTS):
        df = (lf.filter(pl.col("acc_n") % PARTS == p)
                .select("seq", "transaction_id", "account_id", "transaction_type", "status", "amt_c", "bal_c",
                        "transaction_timestamp", "currency")
                .collect(engine="streaming"))
        a = deltas(df, ["seq"])
        b = deltas(df, ["transaction_timestamp", "seq"])
        for frame, store in ((a, by_id_rows), (b, by_ts_rows)):
            store.append(frame.filter(~pl.col("first"))
                         .group_by("transaction_type", "status")
                         .agg(pl.len().alias("n"), (pl.col("delta") == pl.col("expected")).sum().alias("match")))
        # per-account: does id order fully reconcile? does id order equal timestamp order?
        acct_stats.append(
            a.group_by("account_id").agg(
                (~pl.col("first") & (pl.col("delta") != pl.col("expected"))).sum().alias("id_mismatch"),
                (pl.col("bal_c") < 0).sum().alias("negative_balance_rows"),
                pl.col("currency").n_unique().alias("currencies"),
            ).join(
                b.filter(~pl.col("first")).group_by("account_id")
                 .agg((pl.col("delta") != pl.col("expected")).sum().alias("ts_mismatch")), on="account_id")
            .join(
                df.sort("account_id", "seq").group_by("account_id", maintain_order=True)
                  # fixed-width "YYYY-MM-DD HH:MM:SS" strings compare in chronological order;
                  # the first row compares against null and is ignored by sum()
                  .agg((pl.col("transaction_timestamp") < pl.col("transaction_timestamp").shift(1)).sum()
                       .alias("id_order_ts_inversions")),
                on="account_id"))
        rows = df.height
        rss_before_free = psutil.Process().memory_info().rss
        peak = max(peak, rss_before_free)
        del df, a, b
        gc.collect()
        rss_after_free = psutil.Process().memory_info().rss
        print(f"partition {p+1}/{PARTS} rows={rows:,} rss_before_free={rss_before_free/1e9:.2f}GB "
              f"rss_after_free={rss_after_free/1e9:.2f}GB peak={peak/1e9:.2f}GB t={time.time()-t0:.0f}s",
              flush=True)

    def summarize(rows):
        s = pl.concat(rows).group_by("transaction_type", "status").agg(pl.col("n").sum(), pl.col("match").sum())
        return s.with_columns((pl.col("match") / pl.col("n")).alias("match_rate")).sort("transaction_type", "status")

    sid, sts = summarize(by_id_rows), summarize(by_ts_rows)
    acc = pl.concat(acct_stats)
    sid.write_csv(OUT / "ledger_by_transaction_id.csv")
    sts.write_csv(OUT / "ledger_by_timestamp.csv")

    # Transaction id structure
    ids = pl.scan_parquet(RAW).select(
        pl.col("transaction_id").str.contains(r"^TX\d{10}$").sum().alias("ids_matching_TX_10digits"),
        pl.col("transaction_id").str.contains(r"^TX\d{10}-zdl26nr51f60aaa959f$").sum().alias("ids_with_suffix"),
        pl.col("transaction_id").n_unique().alias("unique_ids"),
        pl.col("transaction_id").str.slice(2, 10).n_unique().alias("unique_numeric_parts"),
        pl.col("transaction_id").str.slice(2, 10).cast(pl.Int64).min().alias("min_n"),
        pl.col("transaction_id").str.slice(2, 10).cast(pl.Int64).max().alias("max_n"),
        pl.len().alias("rows")).collect(engine="streaming").to_dicts()[0]
    # Global relationship between id order and time order (row-group order == id order?)
    rel = pl.scan_parquet(RAW).select(
        (pl.col("transaction_id") > pl.col("transaction_id").shift(1)).sum().alias("file_id_increasing_pairs"),
        pl.len().alias("rows"),
        pl.corr(pl.col("transaction_id").str.slice(2, 10).cast(pl.Int64),
                pl.col("transaction_timestamp").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S").dt.epoch("s"),
                method="spearman").alias("spearman_id_vs_time"),
    ).collect().to_dicts()[0]

    tot = lambda s: (int(s["n"].sum()), int(s["match"].sum()))  # noqa: E731
    n_id, m_id = tot(sid)
    n_ts, m_ts = tot(sts)
    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "accounts": acc.height,
        "records_compared_excluding_first_per_account": n_id,
        "by_transaction_id": {"match": m_id, "rate": m_id / n_id},
        "by_timestamp": {"match": m_ts, "rate": m_ts / n_ts},
        "accounts_fully_reconciled_by_id": int((acc["id_mismatch"] == 0).sum()),
        "accounts_fully_reconciled_by_timestamp": int((acc["ts_mismatch"] == 0).sum()),
        "accounts_where_id_order_equals_time_order": int((acc["id_order_ts_inversions"] == 0).sum()),
        "accounts_with_negative_balance_rows": int((acc["negative_balance_rows"] > 0).sum()),
        "accounts_with_multiple_currencies_on_one_balance": int((acc["currencies"] > 1).sum()),
        "transaction_id_structure": ids,
        "id_vs_time_global": rel,
        "peak_rss_gb": round(peak / 1e9, 2),
        "seconds": round(time.time() - t0, 1),
        "per_type_by_id": sid.to_dicts(),
        "per_type_by_timestamp": sts.to_dicts(),
    }
    (OUT / "ledger_semantics.json").write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps({k: v for k, v in result.items() if not k.startswith("per_type")}, indent=2, default=str))
    pl.Config.set_tbl_rows(40)
    print(sid)
    print(sts)


if __name__ == "__main__":
    main()
