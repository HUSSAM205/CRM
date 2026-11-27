"""6. Financial assistant: deterministic intents answered from the same summaries as the dashboard."""
from __future__ import annotations

import streamlit as st

from app.components import alerts
from app.pages.ai_predictions import forecast_for
from app.utils import session
from src.assistant.response_generator import SUPPORTED_EXAMPLES, answer


def render() -> None:
    st.header("Financial assistant")
    st.caption("Answers come only from your validated data summaries. No language model, and no data leaves "
               "this session.")
    if alerts.need_data():
        return
    s = session.get_data()["summaries"]
    acc, cur = st.session_state["account"], st.session_state["currency"]
    st.markdown("**Supported questions:** " + " · ".join(f"*{q}*" for q in SUPPORTED_EXAMPLES))
    q = st.text_input("Ask a question", key="assistant_q", placeholder=SUPPORTED_EXAMPLES[0])
    if st.button("Ask", type="primary") and q.strip():
        text, result = answer(q, s, acc, cur, budgets=st.session_state["budgets"].get(f"active|{acc}|{cur}"),
                              forecast=forecast_for(s, acc, cur))
        st.session_state["assistant_history"].insert(0, (q, text, result.get("intent", "unsupported")))
    for q_, a_, intent in st.session_state["assistant_history"][:10]:
        with st.container(border=True):
            # plain text: user input and answers are never interpreted as Markdown/HTML
            st.text(f"You: {q_}")
            st.text(f"Assistant: {a_}")
            st.caption(f"intent: {intent}")
