"""Assistant regressions from master audit 3 (MA3-03..07): every answer equals the engine's own value."""
from __future__ import annotations

import polars as pl
import pytest

from src.advisor.context import build_context
from src.analytics import insights as I
from src.analytics.aggregation import build_summaries
from src.assistant.advisor_intents import AssistantContext
from src.assistant.response_generator import UNSUPPORTED, answer
from src.data.ingestion import ingest
from src.models.anomaly.anomaly_scoring import review_candidates
from src.utils.configuration import PROJECT_ROOT


@pytest.fixture(scope="module")
def env():
    res, _ = ingest((PROJECT_ROOT / "data/samples/demo_transactions.csv").read_bytes())
    s = build_summaries(res.clean)
    # the account-currency series with the longest history (enough months for anomaly review)
    acc, cur = max(((a, c) for a in s.accounts for c in s.monthly.filter(pl.col("account_id") == a)["currency"].unique()),
                   key=lambda ac: len(s.months(*ac)))
    clean = res.clean.filter((pl.col("account_id") == acc) & (pl.col("currency") == cur))
    return s, acc, cur, AssistantContext(clean=clean)


def _exp(s, acc, cur):
    m = s.monthly.filter((pl.col("account_id") == acc) & (pl.col("currency") == cur))
    return dict(zip(m["month"], m["expenses_cents"]))


def test_compare_this_month_with_last_month(env):
    s, acc, cur, ctx = env
    last = s.months(acc, cur)[-1]          # 'this month' = latest data month; 'last month' = the calendar month before
    y, m = map(int, last.split("-"))
    prev = f"{y - (m == 1):04d}-{12 if m == 1 else m - 1:02d}"
    _, r = answer("Compare this month with last month", s, acc, cur, context=ctx)
    assert r["intent"] == "month_comparison" and r["months"] == [prev, last]
    e = _exp(s, acc, cur)
    assert r["expenses_cents"] == [e.get(prev, 0), e[last]]


def test_highest_months_question_is_not_answered_as_total_spending(env):
    """MA3-04 regression: this question used to return the latest month's total."""
    s, acc, cur, ctx = env
    _, r = answer("Which months had the highest spending?", s, acc, cur, context=ctx)
    assert r["intent"] == "highest_months"
    top = sorted(_exp(s, acc, cur).items(), key=lambda kv: -kv[1])[:3]
    assert [(m, int(v)) for m, v in r["months"]] == [(m, int(v)) for m, v in top]


def test_how_much_can_i_save_uses_the_advisor_surplus_and_states_unknowns(env):
    s, acc, cur, ctx = env
    text, r = answer("How much can I save?", s, acc, cur, context=ctx)
    fc = build_context(ctx.clean, s, acc, cur)
    assert r["intent"] == "savings_capacity" and r["surplus_cents"] == fc.monthly_surplus_cents[0]
    assert "not a bank balance" in text and "Unknown:" in text


def test_why_flagged_shows_the_engine_evidence_and_never_claims_fraud(env):
    s, acc, cur, ctx = env
    text, r = answer("Why was this transaction flagged?", s, acc, cur, context=ctx)
    rc = review_candidates(ctx.clean, acc, cur)
    assert r["intent"] == "flag_explanation"
    assert [x["explanation"] for x in r["items"]] == rc["candidates"].head(3)["explanation"].to_list()
    assert "review recommended" in text and "not" in r["not_fraud"].lower()
    assert "fraud detected" not in text.lower()


@pytest.mark.parametrize("q,name", [("Explain the savings rate", "Net inflow ratio"),
                                    ("What is spending stability?", "Spending stability")])
def test_indicator_explanation_gives_formula_and_engine_value(env, q, name):
    s, acc, cur, ctx = env
    text, r = answer(q, s, acc, cur, context=ctx)
    ref = next(x for x in I.indicators(ctx.clean, s, acc, cur) if x["indicator"].startswith(name))
    assert r["intent"] == "indicator_explanation" and r["specific"]
    assert r["indicators"][0]["value"] == ref["value"] and "Formula:" in text


def test_generic_indicator_question_lists_all_without_a_combined_score(env):
    s, acc, cur, ctx = env
    text, r = answer("Explain this financial indicator", s, acc, cur, context=ctx)
    assert r["intent"] == "indicator_explanation" and not r["specific"] and len(r["indicators"]) >= 3
    assert "no combined score" in text


@pytest.mark.parametrize("q", ["spending", "Spending?", "budget", "money"])
def test_bare_ambiguous_question_asks_for_clarification(env, q):
    s, acc, cur, ctx = env
    text, r = answer(q, s, acc, cur, context=ctx)
    assert r["intent"] == "clarify" and "more specific" in text


@pytest.mark.parametrize("q", ["Should I buy Tesla stock?", "What is my tax liability?", "Should I take a loan?"])
def test_professional_advice_still_refused_with_the_fixed_reply(env, q):
    s, acc, cur, ctx = env
    text, r = answer(q, s, acc, cur, context=ctx)
    assert r["intent"] == "unsupported" and text == UNSUPPORTED and "legal advice" in UNSUPPORTED
