"""Personal Financial AI Analyzer: Streamlit entry point.

Run:  streamlit run app/main.py
Eight sections: the six HW sections plus Financial advisor and Settings (master audit phases 5-8). Navigation uses st.navigation, so the modules in app/pages/
are registered explicitly as callables (Streamlit's automatic pages/ discovery is disabled by it).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from app.components import sidebar  # noqa: E402
from app.pages import (ai_predictions, analytics, budget, financial_advisor, financial_assistant,  # noqa: E402
                       overview, settings, transactions)
from app.utils import session  # noqa: E402

st.set_page_config(page_title="Personal Financial AI Analyzer & Advisor", page_icon="💳", layout="wide")
session.init()
if session.enforce_retention():
    st.toast("Your data was deleted because the retention period ended.")

nav = st.navigation([
    st.Page(overview.render, title="Overview", url_path="overview", default=True),
    st.Page(transactions.render, title="Transactions", url_path="transactions"),
    st.Page(analytics.render, title="Analytics", url_path="analytics"),
    st.Page(ai_predictions.render, title="AI predictions", url_path="ai-predictions"),
    st.Page(budget.render, title="Budget", url_path="budget"),
    st.Page(financial_advisor.render, title="Financial advisor", url_path="advisor"),
    st.Page(financial_assistant.render, title="Financial assistant", url_path="assistant"),
    st.Page(settings.render, title="Settings and privacy", url_path="settings"),
])
sidebar.render()
nav.run()
