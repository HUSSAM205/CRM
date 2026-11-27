"""Category distribution over a period (HW1 F3 'category distribution')."""
from __future__ import annotations

import polars as pl


def category_distribution(category: pl.DataFrame, account: str, currency: str, start: str, end: str) -> pl.DataFrame:
    c = category.filter((pl.col("account_id") == account) & (pl.col("currency") == currency)
                        & pl.col("month").is_between(pl.lit(start), pl.lit(end)))
    tot = c.group_by("merchant_category").agg(pl.col("net_spending_cents").sum())
    positive = tot.filter(pl.col("net_spending_cents") > 0)["net_spending_cents"].sum()
    return tot.with_columns(
        (pl.col("net_spending_cents") / positive if positive else pl.lit(None, dtype=pl.Float64)).alias("share_of_spending")
    ).sort("net_spending_cents", descending=True)
