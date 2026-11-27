"""Consistent warnings and disclaimers."""
from __future__ import annotations

import streamlit as st

DISCLAIMER = ("Educational prototype trained on a public synthetic dataset. Forecasts are estimates, anomaly "
              "results are review candidates (not confirmed fraud), and nothing here is financial advice.")


def budget_alert(level: str, text: str) -> None:
    {"exceeded": st.error, "warning": st.warning}.get(level, st.caption)(text)


def need_data() -> bool:
    if st.session_state.get("data") is None:
        st.info("Load data first: open **Transactions** to upload a CSV or load the demo data.")
        return True
    return False
