"""Display formatting: integer cents -> human-readable money; cents tables -> unit tables."""
from __future__ import annotations

import polars as pl


def money(cents: int | None, currency: str) -> str:
    if cents is None:
        return "—"
    return f"{cents / 100:,.2f} {currency}"


def cents_cols_to_units(df: pl.DataFrame) -> pl.DataFrame:
    """Replace every *_cents column with a 2-dp unit column without the suffix (display only)."""
    return df.with_columns([(pl.col(c) / 100).round(2).alias(c.removesuffix("_cents"))
                            for c in df.columns if c.endswith("_cents")]).drop(
        [c for c in df.columns if c.endswith("_cents")])
