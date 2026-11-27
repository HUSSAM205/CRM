"""Table display helpers (money as currency units, never balance_after)."""
from __future__ import annotations

import polars as pl
import streamlit as st

from app.utils.formatting import cents_cols_to_units

HIDDEN = {"balance_after", "source_row", "amount_cents"}


def show(df: pl.DataFrame, height: int = 360) -> None:
    st.dataframe(cents_cols_to_units(df.drop([c for c in df.columns if c in HIDDEN])),
                 use_container_width=True, hide_index=True, height=height)
