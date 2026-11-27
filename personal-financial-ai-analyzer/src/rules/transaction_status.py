"""Status policy (HW1 F2, HW1 4.5(4), HW2 5.2): only completed records enter totals.

Pending, failed and reversed records are not discarded: they are kept and reported separately.
"""
from __future__ import annotations

import polars as pl

from src.utils.configuration import load_config

COUNTED_STATUSES = frozenset(load_config("financial_rules")["counted_statuses"])
EXCLUDED_STATUSES = frozenset(load_config("financial_rules")["excluded_statuses"])


def is_counted() -> pl.Expr:
    return pl.col("status").str.to_lowercase().is_in(list(COUNTED_STATUSES))


def status_report(df: pl.DataFrame) -> pl.DataFrame:
    """Counts and amounts per status, per currency (amounts in integer cents)."""
    return (df.group_by("currency", "status")
              .agg(pl.len().alias("records"), pl.col("amount_cents").sum().alias("amount_cents"))
              .with_columns(pl.col("status").is_in(list(COUNTED_STATUSES)).alias("in_totals"))
              .sort("currency", "status"))
