"""Assistant (HW2 5.7, 10.4): supported answers equal dashboard values; unsupported -> fixed reply."""
from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from src.analytics.aggregation import build_summaries, period_totals
from src.assistant.intent_detection import detect
from src.assistant.response_generator import UNSUPPORTED, answer
from src.data.validation import validate_transactions

FIX = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture(scope="module")
def s():
    return build_summaries(validate_transactions(pl.read_csv(FIX / "sample_transactions.csv",
                                                             infer_schema=False)).clean)


@pytest.mark.parametrize("q,intent", [
    ("How much did I spend in March?", "total_spending"),
    ("How much did I spend on groceries?", "category_spending"),
    ("Compare January and February.", "month_comparison"),
    ("Am I exceeding my budget?", "budget_status"),
    ("What is my expected spending next month?", "forecast"),
    ("What's the weather today?", "unsupported"),
    ("Should I buy Tesla stock?", "unsupported"),
])
def test_intents(q, intent):
    assert detect(q, ["groceries", "dining", "cash"]).name == intent


def test_total_spending_matches_dashboard(s):
    text, r = answer("How much did I spend in January?", s, "A1", "USD")
    assert r["expenses_cents"] == period_totals(s, "A1", "USD", ["2026-01"])["expenses_cents"] == 13275
    assert text == "Your total spending in 2026-01 was 132.75 USD."


def test_category_spending_hand_value(s):
    text, r = answer("How much did I spend on groceries in January 2026?", s, "A1", "USD")
    assert r["net_spending_cents"] == 8000 and "80.00 USD" in text


def test_month_comparison(s):
    text, r = answer("Compare January and February", s, "A1", "USD")
    assert r["expenses_cents"] == [13275, 20031] and r["difference_cents"] == 6756
    assert "67.56 USD more" in text


def test_budget_status_levels(s):
    _, r = answer("Am I exceeding my budget?", s, "A1", "USD", budgets={"groceries": 3000, "cash": 25000,
                                                                       "dining": 1000})
    levels = {x["category"]: x["level"] for x in r["rows"]}
    assert r["month"] == "2026-02"
    assert levels == {"groceries": "exceeded", "cash": "warning", "dining": "ok"}   # 101%, 80%, negative


def test_unsupported_and_missing_month_never_invent_numbers(s):
    assert answer("Tell me a joke", s, "A1", "USD")[0] == UNSUPPORTED
    text, r = answer("How much did I spend in August?", s, "A1", "USD")
    assert r["error"] == "month_not_in_data" and "not in your data" in text


def test_forecast_reply_passes_through_inference_result(s):
    text, _ = answer("What is my expected spending next month?", s, "A1", "USD",
                     forecast={"eligible": False, "message": "Not enough history for a forecast: 2 active month(s)"})
    assert text.startswith("Not enough history")
