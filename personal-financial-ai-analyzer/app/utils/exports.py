"""CSV report export (HW1 Fig. 2: "dashboard with explanations, warnings, and CSV report")."""
from __future__ import annotations

import io

import polars as pl

from app.utils.formatting import cents_cols_to_units

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def neutralise_formulas(df: pl.DataFrame) -> pl.DataFrame:
    """Spreadsheet formula-injection guard (MA3-13): a text cell starting with = + - @ TAB or CR is prefixed with
    an apostrophe, so Excel/LibreOffice show it as text instead of executing it. Numeric columns are untouched."""
    text = [c for c, t in df.schema.items() if t == pl.String]
    starts = lambda c: pl.any_horizontal([pl.col(c).str.starts_with(p) for p in FORMULA_PREFIXES])
    return df.with_columns([pl.when(starts(c)).then(pl.lit("'") + pl.col(c)).otherwise(pl.col(c)).alias(c)
                            for c in text])


def csv_bytes(df: pl.DataFrame) -> bytes:
    buf = io.BytesIO()
    neutralise_formulas(cents_cols_to_units(df)).write_csv(buf)
    return buf.getvalue()


def monthly_report(summaries, account: str, currency: str) -> bytes:
    m = summaries.monthly.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
    return csv_bytes(m.select("month", "currency", "income_cents", "outflow_cents", "fee_cents", "refund_cents",
                              "expenses_cents", "net_cash_flow_cents", "transfer_cents", "completed_records",
                              "excluded_status_records"))
