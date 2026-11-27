"""Sidebar: data status, account/currency selection, retention and deletion controls."""
from __future__ import annotations

import streamlit as st

from app.utils import session


def render() -> None:
    with st.sidebar:
        st.markdown("### Personal Financial AI Analyzer")
        st.caption("Educational prototype. Not a bank, investment advisor or fraud service.")
        data = session.get_data()
        if data:
            s = data["summaries"]
            st.success(f"Loaded: {data['source']}")
            st.selectbox("Account", s.accounts, key="account")
            acc = st.session_state["account"]
            curs = sorted(s.monthly.filter(s.monthly["account_id"] == acc)["currency"].unique().to_list())
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
