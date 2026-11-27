"""Deterministic financial calculations (HW1 F3, HW2 5.1 step 4).

All money is integer cents (`amount_cents`), so sums are exact; conversion to decimal units
happens only for display. Every aggregate is keyed by currency (src/rules/currency_rules.py).

Definitions (completed records only, see docs/FINANCIAL_RULES.md):
  income_cents        = sum(inflow)                     credit, deposit, interest
  outflow_cents       = sum(outflow)                    debit, withdrawal
  fee_cents           = sum(fee)
  refund_cents        = sum(refund)
  expenses_cents      = outflow + fee - refund
  net_cash_flow_cents = income - expenses
  transfer_cents      = sum(transfer)   reported only; excluded from income/expenses
  category net spend  = outflow - refund  per category (fees reported separately)
Non-completed and 'unresolved' records are excluded from totals and counted separately.
"""
from __future__ import annotations

import polars as pl

from src.rules.currency_rules import require_currency_key
from src.rules.transaction_mapping import FEE, INFLOW, OUTFLOW, REFUND, TRANSFER, UNRESOLVED
from src.rules.transaction_status import is_counted


def _sum_meaning(meaning: str, name: str) -> pl.Expr:
    return (pl.when(is_counted() & (pl.col("meaning") == meaning))
              .then(pl.col("amount_cents")).otherwise(0).sum().alias(name))


def summarize(df: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    """Income/expense summary grouped by `keys` (must include 'currency')."""
    require_currency_key(keys)
    out = (df.group_by(keys)
             .agg(_sum_meaning(INFLOW, "income_cents"),
                  _sum_meaning(OUTFLOW, "outflow_cents"),
                  _sum_meaning(FEE, "fee_cents"),
                  _sum_meaning(REFUND, "refund_cents"),
                  _sum_meaning(TRANSFER, "transfer_cents"),
                  is_counted().sum().alias("completed_records"),
                  (~is_counted()).sum().alias("excluded_status_records"),
                  (is_counted() & (pl.col("meaning") == UNRESOLVED)).sum()
                    .alias("unresolved_type_records"))
             .with_columns((pl.col("outflow_cents") + pl.col("fee_cents") - pl.col("refund_cents"))
                           .alias("expenses_cents"))
             .with_columns((pl.col("income_cents") - pl.col("expenses_cents"))
                           .alias("net_cash_flow_cents"))
             .sort(keys))
    return out


def monthly_summary(df: pl.DataFrame, by_account: bool = True) -> pl.DataFrame:
    keys = (["account_id"] if by_account else []) + ["currency", "month"]
    return summarize(df, keys)


def category_spending(df: pl.DataFrame, by_account: bool = True,
                      by_month: bool = True) -> pl.DataFrame:
    """Refund-adjusted spending per category (outflow - refund; fees excluded)."""
    keys = (["account_id"] if by_account else []) + ["currency"] + \
           (["month"] if by_month else []) + ["merchant_category"]
    require_currency_key(keys)
    return (df.filter(is_counted() & pl.col("meaning").is_in([OUTFLOW, REFUND]))
              .group_by(keys)
              .agg(_sum_meaning(OUTFLOW, "gross_spending_cents"),
                   _sum_meaning(REFUND, "refund_cents"))
              .with_columns((pl.col("gross_spending_cents") - pl.col("refund_cents"))
                            .alias("net_spending_cents"))
              .sort(keys))


def cents_to_units(cents: int) -> float:
    """Display helper: integer cents -> decimal units (2 dp)."""
    return round(cents / 100.0, 2)
