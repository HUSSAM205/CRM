"""Sidebar: data status, account/currency selection, retention and deletion controls."""
from __future__ import annotations

import polars as pl
import streamlit as st

from app.utils import session
from app.utils.formatting import md_escape


def render() -> None:
    with st.sidebar:
        st.markdown("### Personal Financial AI Analyzer")
        st.caption("Educational prototype. Not a bank, investment advisor or fraud service.")
        data = session.get_data()
        if data:
            s = data["summaries"]
            st.success(f"Loaded: {md_escape(data['source'])}")
            st.selectbox("Account", s.accounts, key="account")
            acc = st.session_state["account"]
            by_cur = (s.monthly.filter(s.monthly["account_id"] == acc).group_by("currency")
                       .agg(pl.col("completed_records").sum()).sort(["completed_records", "currency"],
                                                                  descending=[True, False]))
            curs = by_cur["currency"].to_list()          # most-used currency first (default)
            if st.session_state.get("currency") not in curs:
                st.session_state["currency"] = curs[0]
            st.selectbox("Currency", curs, key="currency",
                         help="Amounts in different currencies are never added together.")
        else:
            st.info("No data loaded. Open Transactions to upload a CSV or load the demo.")
        st.divider()
        st.selectbox("Keep my data for", list(session.RETENTION_CHOICES), key="retention")
        if st.button("Delete my data now", disabled=not data):
            session.purge("user request")
            st.rerun()
