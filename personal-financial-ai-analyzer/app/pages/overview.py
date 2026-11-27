"""1. Overview: totals, monthly trend, account/currency filters, CSV report (HW1 F3, Fig. 2)."""
from __future__ import annotations

import polars as pl
import streamlit as st

from app.components import alerts, charts, metrics
from app.utils import exports, session
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
    st.plotly_chart(charts.monthly_trend(m, cur), use_container_width=True)
    st.download_button("Download monthly report (CSV)", exports.monthly_report(s, acc, cur),
                       file_name=f"monthly_report_{cur}.csv", mime="text/csv")
    st.caption(alerts.DISCLAIMER)
