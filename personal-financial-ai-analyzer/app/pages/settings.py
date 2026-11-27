"""8. Settings and privacy: retention, deletion, what is stored and where (HW1 F9, 3.2.4; HW2 6.5;
master audit 12.3). Everything lives in this browser session's memory only."""
from __future__ import annotations

import time

import streamlit as st

from app.utils import session


def _set_retention() -> None:
    st.session_state["retention"] = st.session_state["settings_retention"]


def render() -> None:
    st.header("Settings and privacy")
    data = session.get_data()
    choices = list(session.RETENTION_CHOICES)
    st.selectbox("Keep my data for", choices, index=choices.index(st.session_state["retention"]),
                 key="settings_retention", on_change=_set_retention)
    minutes = session.RETENTION_CHOICES.get(st.session_state["retention"])
    if data:
        left = None if minutes is None else max(0, int(minutes * 60 - (time.time() - data["loaded_at"])))
        st.write(f"Your data will be deleted {'when you close this tab' if left is None else f'in about {left // 60} min'}"
                 " or when you press the button below.")
    st.subheader("What this app holds right now")
    ss = st.session_state
    rows = 0 if not data else data["clean"].height
    st.text(f"Transactions: {rows:,} valid rows" + (f" ({data['rejected'].height:,} rejected)" if data else "") + "\n"
            f"Budgets set: {sum(1 for k in ss['budgets'] if not k.startswith('active|'))}\n"
            f"Savings goals: {len(ss['goals'])}\n"
            f"Personal facts entered: {sum(1 for v in ss['user_facts'].values() if v is not None)}\n"
            f"Assistant questions: {len(ss['assistant_history'])}")
    if st.button("Delete all my data", key="settings_delete", disabled=not (data or ss["goals"] or ss["user_facts"])):
        session.purge("user request (settings)")
        st.success("All uploaded transactions, budgets, goals, facts and questions were deleted from this session.")
        st.rerun()
    st.subheader("How your data is handled")
    st.markdown(
        "- **Where:** only in the memory of this browser session on the computer running the app. Nothing is "
        "written to disk, and a page reload starts an empty session.\n"
        "- **Training:** your file is never added to any training data; models were trained once on a public "
        "synthetic dataset and are only loaded here.\n"
        "- **External services:** none. No AI provider, analytics or telemetry receives your data "
        "(Streamlit usage statistics are switched off).\n"
        "- **Logs:** record only counts and events, never transaction values or account identifiers.\n"
        "- **Other users:** each browser session is isolated; nobody else can see your data.")
