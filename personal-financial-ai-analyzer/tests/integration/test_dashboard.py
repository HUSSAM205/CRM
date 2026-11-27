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
                                  "financial_advisor", "financial_assistant", "settings"])
def test_every_page_renders_without_exception(page, demo_state):
    at = seeded(page, demo_state)
    assert not at.exception, at.exception


@pytest.mark.parametrize("page", ["overview", "analytics", "ai_predictions", "budget", "financial_advisor",
                                  "financial_assistant"])
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
    assert any(f"{expected / 100:,.2f} USD" in t.value for t in at.text)   # answers render as plain text


def test_budget_page_alerts_and_editing(demo_state):
    at = seeded("budget", demo_state)
    assert not at.exception
    key = [k for k in at.session_state["budgets"] if k.startswith("active|")]
    assert key, "budget page must publish budgets for the assistant"


def test_ai_page_shows_outlook_with_quality_gate_and_unusual_label(demo_state):
    """Master audit 7.7/7.12: the page shows the deterministic outlook (value equal to outlook_next), states
    that ML forecasting was not effective, and labels anomalies as review recommendations, never fraud."""
    import polars as pl

    from src.models.forecasting.inference import outlook_next
    at = seeded("ai_predictions", demo_state)
    assert not at.exception
    s, acc = demo_state["summaries"], demo_state["summaries"].accounts[0]
    f = outlook_next(s.monthly.filter((pl.col("account_id") == acc) & (pl.col("currency") == "USD")))
    assert f["eligible"]
    shown = {m.label: m.value for m in at.metric}
    assert shown[f"Typical spending for {f['target_month']}"] == f"{f['point_cents'] / 100:,.2f} USD"
    assert any("NOT EFFECTIVE" in i.value for i in at.info)
    assert any("Unusual transaction — review recommended." in w.value and "not a fraud finding" in w.value
               for w in at.warning)
    assert not any("fraud detected" in x.value.lower() for x in [*at.warning, *at.info, *at.caption, *at.markdown])


def test_delete_button_purges_session(demo_state):
    at = seeded("overview", demo_state)
    at.sidebar.button[0].click().run()
    assert at.session_state["data"] is None if "data" in at.session_state else True
    assert any("Load data first" in i.value for i in at.info)


def test_budget_editor_initial_values_are_suggestions_in_currency_units(demo_state):
    """Regression (K-15): unsaved budgets were shown in cents (100x too high)."""
    from src.budget.budget_calculator import suggest_budgets
    at = seeded("budget", demo_state)
    s, acc = demo_state["summaries"], demo_state["summaries"].accounts[0]
    month = s.months(acc, "USD")[-1]
    sug = suggest_budgets(s.category, acc, "USD", month)
    stored = at.session_state["budgets"][f"active|{acc}|USD"]
    assert stored == dict(zip(sug["merchant_category"], sug["suggested_cents"]))


def test_transactions_date_filter(demo_state):
    """HW1 S7 / 3.2.1: transactions can be filtered by date (audit gap A-02)."""
    import datetime as dt

    import polars as pl
    at = seeded("transactions", demo_state)
    acc = demo_state["summaries"].accounts[0]
    view = demo_state["clean"].filter((pl.col("account_id") == acc) & (pl.col("currency") == "USD"))
    before = next(c.value for c in at.caption if "transactions." in c.value)
    last = view["transaction_timestamp"].max().date()            # the widget's max_value
    at.date_input(key="tx_dates").set_value((dt.date(2026, 1, 1), last)).run()
    after = next(c.value for c in at.caption if "transactions." in c.value)
    expected = view.filter(pl.col("transaction_timestamp").dt.date() >= dt.date(2026, 1, 1)).height
    assert before.startswith(f"{view.height} transactions.") and after.startswith(f"{expected} transactions.")
    assert expected < view.height


def test_saved_budget_changes_drive_alerts_and_assistant(demo_state):
    """Server side of 'change a budget': a stored (edited) budget must drive progress, alerts and the assistant."""
    from src.assistant.response_generator import answer
    from src.budget.budget_calculator import suggest_budgets
    s, acc = demo_state["summaries"], demo_state["summaries"].accounts[0]
    month = "2026-06"
    sug = suggest_budgets(s.category, acc, "USD", month)
    edited = dict(zip(sug["merchant_category"], sug["suggested_cents"]))
    edited["dining"] = 1                                     # user sets dining to 0.01
    at = page_app("budget")
    at.session_state["data"], at.session_state["account"], at.session_state["currency"] = demo_state, acc, "USD"
    at.session_state["budgets"] = {f"{acc}|USD|{month}": edited}
    at.session_state["bud_month"] = month
    at.run()
    assert any("dining" in e.value and "Over budget" in e.value for e in at.error)
    assert at.session_state["budgets"][f"active|{acc}|USD"]["dining"] == 1
    text, r = answer("Am I exceeding my budget?", s, acc, "USD", budgets=at.session_state["budgets"][f"active|{acc}|USD"])
    # the assistant reports the LATEST data month (2026-07), where dining spending is 0 -> "ok", not exceeded
    assert r["month"] == "2026-07"
    assert next(x for x in r["rows"] if x["category"] == "dining")["level"] == "ok"


def test_analytics_tabs_show_values_equal_to_insights(demo_state):
    """Master audit 6.2-6.7: each analytics tab renders and its numbers come from src.analytics.insights."""
    from src.analytics import insights as I
    at = seeded("analytics", demo_state)
    assert not at.exception
    s, acc = demo_state["summaries"], demo_state["summaries"].accounts[0]
    assert [t.label for t in at.tabs] == ["Categories", "Spending over time", "Income and cash flow",
                                          "Recurring and behaviour", "Indicators"]
    st_ = I.spending_statistics(s, acc, "USD")
    shown = {m.label: m.value for m in at.metric}
    assert shown["Average month"] == f"{st_['mean_cents'] / 100:,.2f} USD"
    assert shown["Median month"] == f"{st_['median_cents'] / 100:,.2f} USD"
    inc = I.income_analysis(demo_state["clean"], s, acc, "USD")
    assert shown["Months with recorded inflows"] == f"{inc['months_with_inflows']} of {inc['months']}"
    assert any("not a bank balance" in c.value for c in at.caption)
    assert not any("health score" == x.value.lower() for x in at.metric)


def test_overview_month_over_month_equals_monthly_table(demo_state):
    import polars as pl
    at = seeded("overview", demo_state)
    s, acc = demo_state["summaries"], demo_state["summaries"].accounts[0]
    ms = s.months(acc, "USD")
    m = s.monthly.filter((pl.col("account_id") == acc) & (pl.col("currency") == "USD")
                         & pl.col("month").is_in(ms[-2:])).sort("month")["expenses_cents"].to_list()
    met = next(x for x in at.metric if x.label == f"Expenses in {ms[-1]} vs {ms[-2]}")
    assert met.value == f"{m[1] / 100:,.2f} USD"
    assert any("not a verified bank balance" in c.value for c in at.caption)


def test_advisor_page_goal_flow_and_values_equal_engine(demo_state):
    """Analyzer -> Advisor: the page's surplus equals the engine; adding a goal shows the deterministic plan."""
    from src.advisor import savings as S
    from src.advisor.context import build_context
    at = seeded("financial_advisor", demo_state)
    assert not at.exception
    s, acc = demo_state["summaries"], demo_state["summaries"].accounts[0]
    ctx = build_context(demo_state["clean"], s, acc, "USD")
    shown = {m.label: m.value for m in at.metric}
    assert shown["Average monthly surplus"] == f"{ctx.monthly_surplus_cents[0] / 100:,.2f} USD"
    assert [t.label for t in at.tabs] == ["Recommendations", "Savings goals", "What-if scenarios", "Can I afford this?"]
    form_inputs = [w for w in at.text_input if w.label == "Goal name"]
    form_inputs[0].set_value("Bike")
    next(w for w in at.number_input if w.label == "Target amount (USD)").set_value(600.0)
    next(w for w in at.number_input if w.label == "Already saved (USD)").set_value(100.0)
    next(w for w in at.text_input if w.label.startswith("Target month")).set_value("2027-01")
    next(b for b in at.button if b.label == "Add goal").click().run()
    assert not at.exception
    assert at.session_state["goals"][0]["target_cents"] == 60000
    p = S.plan(S.Goal(**at.session_state["goals"][0]), ctx.window[-1], ctx)
    assert any(f"{p['required_monthly_cents'] / 100:,.2f} USD" in t.value for t in at.text)
    # affordability without a balance is never confirmed
    next(w for w in at.number_input if w.label == "Purchase amount (USD)").set_value(250.0).run()
    assert any("Cannot confirm affordability" in w.value for w in at.warning)


def test_advisor_invalid_goal_month_is_rejected(demo_state):
    at = seeded("financial_advisor", demo_state)
    next(w for w in at.text_input if w.label == "Goal name").set_value("X")
    next(w for w in at.text_input if w.label.startswith("Target month")).set_value("2027-13")
    next(b for b in at.button if b.label == "Add goal").click().run()
    assert at.session_state["goals"] == [] and any("target month" in e.value for e in at.error)


def test_settings_delete_purges_goals_facts_and_data(demo_state):
    at = seeded("settings", demo_state, goals=[{"name": "G", "kind": "savings", "target_cents": 100, "saved_cents": 0,
                                                "target_month": None, "monthly_contribution_cents": None}],
                user_facts={"bal": 10.0, "sav": None, "inc": None, "obl": None})
    assert any("Savings goals: 1" in t.value for t in at.text)
    next(b for b in at.button if b.label == "Delete all my data").click().run()
    assert at.session_state["goals"] == [] and at.session_state["user_facts"] == {}
    assert at.session_state["data"] is None if "data" in at.session_state else True


def test_settings_retention_choice_updates_session(demo_state):
    at = seeded("settings", demo_state)
    at.selectbox(key="settings_retention").set_value("15 minutes").run()
    assert at.session_state["retention"] == "15 minutes"
