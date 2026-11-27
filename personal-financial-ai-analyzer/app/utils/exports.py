"""CSV report export (HW1 Fig. 2: "dashboard with explanations, warnings, and CSV report")."""
from __future__ import annotations

import io

import polars as pl

from app.utils.formatting import cents_cols_to_units


def csv_bytes(df: pl.DataFrame) -> bytes:
    buf = io.BytesIO()
    cents_cols_to_units(df).write_csv(buf)
    return buf.getvalue()


def monthly_report(summaries, account: str, currency: str) -> bytes:
    m = summaries.monthly.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
    return csv_bytes(m.select("month", "currency", "income_cents", "outflow_cents", "fee_cents", "refund_cents",
                              "expenses_cents", "net_cash_flow_cents", "transfer_cents", "completed_records",
                              "excluded_status_records"))
