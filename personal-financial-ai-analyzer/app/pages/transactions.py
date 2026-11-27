"""2. Transactions: upload, mapping, validation report, filters, table (HW1 F1, S7; HW2 Table 10.1)."""
from __future__ import annotations

import polars as pl
import streamlit as st

from app.components import tables, upload
from app.utils import session
from app.utils.validation import explain


def render() -> None:
    st.header("Transactions")
    upload.render()
    d = session.get_data()
    if not d:
        return
    st.divider()
    clean, rej = d["clean"], d["rejected"]
    c1, c2 = st.columns(2)
    c1.metric("Valid rows", f"{clean.height:,}")
    c2.metric("Rejected rows", f"{rej.height:,}")
    if rej.height:
        with st.expander("Why rows were rejected", expanded=True):
            counts = rej.group_by("reject_reason").len().sort("len", descending=True)
            st.dataframe(counts.with_columns(pl.col("reject_reason").map_elements(explain, return_dtype=pl.String)
                                             .alias("explanation")), hide_index=True, use_container_width=True)
            tables.show(rej.with_columns((pl.col("source_row") + 2).alias("file_line")).head(200), height=240)
    acc, cur = st.session_state["account"], st.session_state["currency"]
    view = clean.filter((pl.col("account_id") == acc) & (pl.col("currency") == cur))
    f1, f2, f3 = st.columns(3)
    cats = f1.multiselect("Category", sorted(view["merchant_category"].unique().to_list()), key="tx_cat")
    types = f2.multiselect("Type", sorted(view["transaction_type"].unique().to_list()), key="tx_type")
    stats = f3.multiselect("Status", sorted(view["status"].unique().to_list()), key="tx_status")
    if cats:
        view = view.filter(pl.col("merchant_category").is_in(cats))
    if types:
        view = view.filter(pl.col("transaction_type").is_in(types))
    if stats:
        view = view.filter(pl.col("status").is_in(stats))
    st.caption(f"{view.height:,} transactions. 'meaning' shows how each row is counted.")
    tables.show(view.sort("transaction_timestamp", descending=True)
                .select("transaction_timestamp", "transaction_type", "meaning", "merchant_category", "amount",
                        "currency", "status", "transaction_id"))
