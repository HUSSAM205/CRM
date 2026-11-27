"""Account-relative transaction features for anomaly ranking (HW2 5.5).

Features (configs/anomaly_detection.yaml):
  log_amount                         ln(amount)
  hour, day_of_week                  from transaction_timestamp (ISO weekday 1-7)
  category_history_share             share of the account's HISTORY records in this category
                                     (numeric encoding of merchant_category; 0 if never seen)
  log_amount_to_category_median      ln(amount / median amount of the account's HISTORY records in
                                     this category); falls back to the account-wide history median
History = the account's completed spending records strictly before the scored period
(docs/leakage_analysis.md L8). balance_after is never used (D-03).
"""
from __future__ import annotations

import polars as pl

SPEND_TYPES = ["debit", "withdrawal", "fee"]
FEATURES = ["log_amount", "hour", "day_of_week", "category_history_share", "log_amount_to_category_median"]


def spending(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter((pl.col("status") == "completed") & pl.col("transaction_type").is_in(SPEND_TYPES))


def history_stats(history: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Per (account, category) and per account statistics from history rows."""
    acc = history.group_by("account_id").agg(pl.len().alias("acc_n"), pl.col("amount").median().alias("acc_median"),
                                             pl.col("amount").log().median().alias("acc_log_median"),
                                             (pl.col("amount").log() - pl.col("amount").log().median()).abs()
                                               .median().alias("acc_log_mad"))
    cat = history.group_by("account_id", "merchant_category").agg(pl.len().alias("cat_n"),
                                                                  pl.col("amount").median().alias("cat_median"))
    return acc, cat


def build_features(rows: pl.DataFrame, acc: pl.DataFrame, cat: pl.DataFrame) -> pl.DataFrame:
    out = (rows.join(acc, on="account_id", how="left")
               .join(cat, on=["account_id", "merchant_category"], how="left")
               .with_columns(pl.col("cat_n").fill_null(0),
                             pl.coalesce("cat_median", "acc_median").alias("ref_median")))
    return out.with_columns(
        pl.col("amount").log().alias("log_amount"),
        pl.col("transaction_timestamp").dt.hour().cast(pl.Float64).alias("hour"),
        pl.col("transaction_timestamp").dt.weekday().cast(pl.Float64).alias("day_of_week"),
        (pl.col("cat_n") / pl.col("acc_n")).fill_null(0.0).alias("category_history_share"),
        (pl.col("amount") / pl.col("ref_median")).log().fill_null(0.0).alias("log_amount_to_category_median"),
    )
