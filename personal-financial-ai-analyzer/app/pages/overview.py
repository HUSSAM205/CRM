"""1. Overview: totals, monthly trend, account/currency filters, CSV report (HW1 F3, Fig. 2)."""
from __future__ import annotations

import polars as pl
import streamlit as st

from app.components import alerts, charts, metrics, tables
from app.utils import exports, session
from app.utils.formatting import md_escape, money
from src.analytics.category_analysis import category_distribution
from src.analytics.aggregation import period_totals


def render() -> None:
    st.header("Overview")
    if alerts.need_data():
        return
    d = session.get_data()
    s, acc, cur = d["summaries"], st.session_state["account"], st.session_state["currency"]
    months = s.months(acc, cur)
    a, b = st.select_slider("Period", options=months, value=(months[0], months[-1]), key="ov_period")
    sel = [m for m in months if a <= m <= b]
    t = period_totals(s, acc, cur, sel)
    metrics.kpi_row(t, cur)
    if t["excluded_status_records"]:
        st.caption(f"{t['excluded_status_records']} pending, failed or reversed record(s) are excluded from "
                   "these totals.")
    m = s.monthly.filter((pl.col("account_id") == acc) & (pl.col("currency") == cur) & pl.col("month").is_in(sel))
    st.plotly_chart(charts.monthly_trend(m, cur), width="stretch")
    st.caption(f"Data available: {months[0]} to {months[-1]} ({len(months)} months with records). Net cash flow is "
               "derived from transactions; it is **not a verified bank balance**.")
    if len(sel) >= 2:
        last2 = s.monthly.filter((pl.col("account_id") == acc) & (pl.col("currency") == cur)
                                 & pl.col("month").is_in(sel[-2:])).sort("month")
        if last2.height == 2:
            e0, e1 = last2["expenses_cents"].to_list()
            st.metric(f"Expenses in {sel[-1]} vs {sel[-2]}", money(e1, cur), delta=money(e1 - e0, cur),
                      delta_color="inverse")
    top = category_distribution(s.category, acc, cur, a, b).head(3)
    if top.height:
        st.write("Largest expense categories in the period: " + ", ".join(
            f"**{md_escape(r['merchant_category'])}** {money(r['net_spending_cents'], cur)}" for r in top.iter_rows(named=True)))
    with st.expander("Recent activity"):
        recent = (d["clean"].filter((pl.col("account_id") == acc) & (pl.col("currency") == cur))
                    .sort("transaction_timestamp", descending=True).head(10)
                    .select("transaction_timestamp", "transaction_type", "merchant_category", "amount", "status"))
        tables.show(recent, height=300)
    st.download_button("Download monthly report (CSV)", exports.monthly_report(s, acc, cur),
                       file_name=f"monthly_report_{cur}.csv", mime="text/csv")
    st.caption(alerts.DISCLAIMER)
