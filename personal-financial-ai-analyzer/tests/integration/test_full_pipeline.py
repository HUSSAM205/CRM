"""Full user pipeline on the public-data demo file: ingest -> summaries -> budget -> forecast ->
anomaly candidates -> assistant, with cross-component consistency checks."""
from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from src.analytics.aggregation import build_summaries, period_totals
from src.assistant.response_generator import answer
from src.budget.budget_calculator import suggest_budgets
from src.data.ingestion import ingest
from src.models.anomaly.anomaly_scoring import LABEL, review_candidates
from src.models.forecasting.inference import forecast_next

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "data/samples/demo_transactions.csv"
pytestmark = pytest.mark.skipif(not DEMO.exists(), reason="demo sample not prepared")


def test_demo_pipeline_end_to_end():
    res, _ = ingest(DEMO.read_bytes())
    assert res.rejected.is_empty() and res.clean.height == 195
    s = build_summaries(res.clean)
    acc = s.accounts[0]
    months = s.months(acc, "USD")
    # budgets: suggestion equals the median rule, and the assistant reads the same numbers
    b = suggest_budgets(s.category, acc, "USD", months[-1])
    budgets = dict(zip(b["merchant_category"], b["suggested_cents"]))
    _, r = answer("Am I exceeding my budget?", s, acc, "USD", budgets=budgets)
    for row in r["rows"]:
        spent = b.filter(pl.col("merchant_category") == row["category"])["spent_current_cents"][0]
        assert row["spent_cents"] == spent
    # forecast: eligible USD history (demo accounts were chosen from forecast-eligible series)
    f = forecast_next(s.monthly.filter((pl.col("account_id") == acc) & (pl.col("currency") == "USD")))
    assert f["eligible"]
    text, rf = answer("What is my expected spending next month?", s, acc, "USD", forecast=f)
    assert rf["forecast_cents"] == f["forecast_cents"] and "estimate" in text
    # anomaly candidates are labelled as review candidates
    a = review_candidates(res.clean, acc, "USD")
    assert a["ok"] and a["label"] == LABEL and a["candidates"].height > 0
    # totals equal sum of monthly cells
    assert period_totals(s, acc, "USD")["expenses_cents"] == int(
        s.monthly.filter((pl.col("account_id") == acc) & (pl.col("currency") == "USD"))["expenses_cents"].sum())
