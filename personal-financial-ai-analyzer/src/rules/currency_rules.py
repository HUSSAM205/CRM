"""Currency separation (HW1 R6, HW2 Table 7.1): amounts are never summed across currencies.

No exchange-rate conversion exists in this project, so every aggregate key includes `currency`.
"""
from __future__ import annotations

import polars as pl


class MixedCurrencyError(ValueError):
    """Raised when a computation would combine different currencies."""


def require_currency_key(keys: list[str] | tuple[str, ...]) -> None:
    if "currency" not in keys:
        raise MixedCurrencyError(f"aggregation keys {list(keys)} omit 'currency'")


def single_currency(df: pl.DataFrame) -> str:
    """Return the only currency in df, or raise if there are several."""
    values = df.get_column("currency").unique().to_list()
    if len(values) != 1:
        raise MixedCurrencyError(f"expected one currency, found {sorted(map(str, values))}")
    return values[0]
