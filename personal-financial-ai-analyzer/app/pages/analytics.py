"""3. Analytics: category distribution, monthly category spending, trends, month comparison."""
from __future__ import annotations

import polars as pl
import streamlit as st

from app.components import alerts, charts, tables
from app.utils import session
from src.analytics.category_analysis import category_distribution
from src.analytics.monthly_analysis import compare_months


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
    tot = category_distribution(s.category, acc, cur, a, b)
    left, right = st.columns(2)
    left.plotly_chart(charts.category_bar(tot, cur, f"Spending by category, {a} to {b}"), width="stretch")
    right.plotly_chart(charts.category_stacked(c, cur), width="stretch")
    st.caption("Category spending = purchases minus refunds in that category. Fees are reported separately.")

    st.subheader("Compare two months")
    x1, x2 = st.columns(2)
    m1 = x1.selectbox("First month", months, index=max(0, len(months) - 2), key="cmp1")
    m2 = x2.selectbox("Second month", months, index=len(months) - 1, key="cmp2")
    piv = compare_months(s.category, acc, cur, m1, m2)
    if not piv.is_empty():
        tables.show(piv, height=300)
