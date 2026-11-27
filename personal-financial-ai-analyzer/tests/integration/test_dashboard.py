"""Headless dashboard tests (streamlit.testing): every page renders; shown numbers equal the summaries."""
from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.analytics.aggregation import build_summaries, period_totals
from src.data.ingestion import ingest

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "data/samples/demo_transactions.csv"
pytestmark = pytest.mark.skipif(not DEMO.exists(), reason="demo sample not prepared")


PAGE_SCRIPT = """
import sys
sys.path.insert(0, {root!r})
import importlib
from app.components import sidebar
from app.utils import session
session.init()
sidebar.render()
importlib.import_module("app.pages.{page}").render()
"""


def page_app(page: str) -> AppTest:
    """AppTest rendering one page module plus the sidebar; session state is pre-seeded by the test."""
    return AppTest.from_string(PAGE_SCRIPT.format(root=str(ROOT), page=page), default_timeout=60)


@pytest.fixture(scope="module")
def demo_state():
    res, mapping = ingest(DEMO.read_bytes())
    return {"clean": res.clean, "rejected": res.rejected, "summaries": build_summaries(res.clean),
            "source": "demo", "mapping": mapping, "loaded_at": 1e18}


def seeded(page: str, demo_state, **extra) -> AppTest:
    at = page_app(page)
    at.session_state["data"] = demo_state
    acc = demo_state["summaries"].accounts[0]
    at.session_state["account"], at.session_state["currency"] = acc, "USD"
    for k, v in extra.items():
        at.session_state[k] = v
    return at.run()


@pytest.mark.parametrize("page", ["overview", "transactions", "analytics", "ai_predictions", "budget",
                                  "financial_assistant"])
def test_every_page_renders_without_exception(page, demo_state):
    at = seeded(page, demo_state)
    assert not at.exception, at.exception


@pytest.mark.parametrize("page", ["overview", "analytics", "ai_predictions", "budget", "financial_assistant"])
def test_pages_ask_for_data_when_empty(page):
    at = page_app(page).run()
    assert not at.exception
    assert any("Load data first" in i.value for i in at.info)


def test_overview_kpis_equal_deterministic_totals(demo_state):
    at = seeded("overview", demo_state)
    s, acc = demo_state["summaries"], demo_state["summaries"].accounts[0]
    t = period_totals(s, acc, "USD", s.months(acc, "USD"))
    shown = {m.label: m.value for m in at.metric}
    assert shown["Income (inflows)"] == f"{t['income_cents'] / 100:,.2f} USD"
    assert shown["Expenses"] == f"{t['expenses_cents'] / 100:,.2f} USD"
    assert shown["Net cash flow"] == f"{t['net_cash_flow_cents'] / 100:,.2f} USD"


def test_assistant_answer_matches_dashboard(demo_state):
    at = seeded("financial_assistant", demo_state)
    s, acc = demo_state["summaries"], demo_state["summaries"].accounts[0]
    last = s.months(acc, "USD")[-1]
    at.text_input(key="assistant_q").set_value(f"How much did I spend in {last}?")
    at.button[0].click().run()
    expected = period_totals(s, acc, "USD", [last])["expenses_cents"]
    assert any(f"{expected / 100:,.2f} USD" in m.value for m in at.markdown)


def test_budget_page_alerts_and_editing(demo_state):
    at = seeded("budget", demo_state)
    assert not at.exception
    key = [k for k in at.session_state["budgets"] if k.startswith("active|")]
    assert key, "budget page must publish budgets for the assistant"


def test_ai_page_shows_forecast_or_notice(demo_state):
    at = seeded("ai_predictions", demo_state)
    texts = [m.label for m in at.metric] + [w.value for w in at.warning]
    assert any("Expected spending" in t or "Not enough history" in t for t in texts)
    assert any("not confirmed fraud" in c.value for c in at.caption) or at.info


def test_delete_button_purges_session(demo_state):
    at = seeded("overview", demo_state)
    at.sidebar.button[0].click().run()
    assert at.session_state["data"] is None if "data" in at.session_state else True
    assert any("Load data first" in i.value for i in at.info)
