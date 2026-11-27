"""Month-level comparisons used by the Analytics page and the assistant (HW1 F3)."""
from __future__ import annotations

import polars as pl


def compare_months(category: pl.DataFrame, account: str, currency: str, m1: str, m2: str) -> pl.DataFrame:
    """Per-category net spending in two months and the change m2 - m1 (missing = 0)."""
    c = category.filter((pl.col("account_id") == account) & (pl.col("currency") == currency)
                        & pl.col("month").is_in([m1, m2]))
    cats = sorted(c["merchant_category"].unique().to_list())
    rows = []
    for cat in cats:
        v = {m: int(c.filter((pl.col("merchant_category") == cat) & (pl.col("month") == m))["net_spending_cents"].sum())
             for m in (m1, m2)}
        rows.append({"merchant_category": cat, f"{m1}_cents": v[m1], f"{m2}_cents": v[m2],
                     "change_cents": v[m2] - v[m1]})
    schema = {"merchant_category": pl.String, f"{m1}_cents": pl.Int64, f"{m2}_cents": pl.Int64, "change_cents": pl.Int64}
    return pl.DataFrame(rows, schema=schema).sort("change_cents")
