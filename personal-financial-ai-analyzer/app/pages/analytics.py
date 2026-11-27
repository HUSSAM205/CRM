"""3. Analytics: category distribution, monthly category spending, trends, month comparison."""
from __future__ import annotations

import polars as pl
import streamlit as st

from app.components import alerts, charts, tables
from app.utils import session


def render() -> None:
    st.header("Analytics")
    if alerts.need_data():
        return
    s = session.get_data()["summaries"]
    acc, cur = st.session_state["account"], st.session_state["currency"]
    months = s.months(acc, cur)
    a, b = st.select_slider("Period", options=months, value=(months[max(0, len(months) - 6)], months[-1]),
                            key="an_period")
    c = s.category.filter((pl.col("account_id") == acc) & (pl.col("currency") == cur)
                          & pl.col("month").is_between(pl.lit(a), pl.lit(b)))
    tot = c.group_by("merchant_category").agg(pl.col("net_spending_cents").sum())
    left, right = st.columns(2)
    left.plotly_chart(charts.category_bar(tot, cur, f"Spending by category, {a} to {b}"), use_container_width=True)
    right.plotly_chart(charts.category_stacked(c, cur), use_container_width=True)
    st.caption("Category spending = purchases minus refunds in that category. Fees are reported separately.")

    st.subheader("Compare two months")
    x1, x2 = st.columns(2)
    m1 = x1.selectbox("First month", months, index=max(0, len(months) - 2), key="cmp1")
    m2 = x2.selectbox("Second month", months, index=len(months) - 1, key="cmp2")
    both = s.category.filter((pl.col("account_id") == acc) & (pl.col("currency") == cur)
                             & pl.col("month").is_in([m1, m2]))
    if not both.is_empty():
        piv = (both.pivot(on="month", index="merchant_category", values="net_spending_cents", aggregate_function="sum")
                   .fill_null(0))
        for m in (m1, m2):
            if m not in piv.columns:
                piv = piv.with_columns(pl.lit(0).alias(m))
        piv = piv.select("merchant_category", pl.col(m1).alias(f"{m1}_cents"), pl.col(m2).alias(f"{m2}_cents"),
                         (pl.col(m2) - pl.col(m1)).alias("change_cents"))
        tables.show(piv.sort("change_cents"), height=300)
