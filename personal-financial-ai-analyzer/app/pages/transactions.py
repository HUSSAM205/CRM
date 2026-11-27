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
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Input rows", f"{clean.height + rej.height:,}")
    c2.metric("Valid rows", f"{clean.height:,}")
    c3.metric("Rejected rows", f"{rej.height:,}")
    reasons = rej["reject_reason"] if rej.height else pl.Series([], dtype=pl.String)
    c4.metric("Duplicates", f"{int((reasons == 'duplicate_transaction_id').sum()):,}")
    if rej.height:
        groups = {"missing fields": reasons.str.starts_with("missing_"),
                  "parsing failures": reasons.is_in(["invalid_timestamp", "invalid_amount", "amount_precision"]),
                  "unsupported values": reasons.is_in(["unknown_currency", "unknown_status", "amount_out_of_range",
                                                       "negative_amount"])}
        st.caption(" · ".join(f"{k}: {int(v.sum()):,}" for k, v in groups.items()) +
                   ". Every rejected row is listed below; none is dropped silently.")
    if rej.height:
        with st.expander("Why rows were rejected", expanded=True):
            counts = rej.group_by("reject_reason").len().sort("len", descending=True)
            # plain text (not a canvas table) so the reasons are readable by screen readers
            st.markdown("\n".join(f"- **{n}** row(s): {explain(r)}" for r, n in counts.iter_rows()))
            tables.show(rej.with_columns((pl.col("source_row") + 2).alias("file_line")).head(200), height=240)
    acc, cur = st.session_state["account"], st.session_state["currency"]
    view = clean.filter((pl.col("account_id") == acc) & (pl.col("currency") == cur))
    if not view.is_empty():
        d0, d1 = view["transaction_timestamp"].min().date(), view["transaction_timestamp"].max().date()
        rng = st.date_input("Date range", value=(d0, d1), min_value=d0, max_value=d1, key="tx_dates")
        if isinstance(rng, (tuple, list)) and len(rng) == 2:
            view = view.filter(pl.col("transaction_timestamp").dt.date().is_between(pl.lit(rng[0]), pl.lit(rng[1])))
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
