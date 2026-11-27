"""Preprocessing of one batch of raw transactions into derived tables (Gate 4; HW1/HW2 4.5).

Used by scripts/workers/aggregate_partition.py (one account partition per process) and by tests.
Steps: validate (types, timestamps, currency, status, dedup by transaction_id, rejection reasons) ->
monthly account x currency summary -> category spending -> per-series activity by split period.
"""
from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from src.analytics.financial_metrics import category_spending, monthly_summary
from src.data.validation import ValidationResult, validate_transactions
from src.experiments.data_splitting import period_expr


@dataclass
class PartitionOutput:
    validation: ValidationResult
    monthly: pl.DataFrame
    category: pl.DataFrame
    series_stats: pl.DataFrame


def series_activity(monthly: pl.DataFrame) -> pl.DataFrame:
    """Active spending months (>= 1 completed debit/withdrawal/fee) per account-currency per period."""
    active = (pl.col("outflow_cents") + pl.col("fee_cents")) > 0
    return (monthly.group_by("account_id", "currency")
                   .agg(*[(active & (pl.col("period") == p)).sum().alias(f"{p}_active_months")
                          for p in ("train", "validation", "test")]))


def process_partition(raw: pl.DataFrame) -> PartitionOutput:
    res = validate_transactions(raw)
    ms = monthly_summary(res.clean).with_columns(period_expr("month").alias("period"))
    return PartitionOutput(res, ms, category_spending(res.clean), series_activity(ms))
