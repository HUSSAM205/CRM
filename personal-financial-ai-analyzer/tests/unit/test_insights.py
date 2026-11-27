"""Analyzer insights (master audit 6.2-6.7) on a hand-built ledger with known answers."""
from __future__ import annotations

from datetime import datetime, timedelta

import polars as pl
import pytest

from src.analytics import insights as I
from src.analytics.aggregation import build_summaries
from src.data.validation import validate_transactions


def ledger() -> pl.DataFrame:
    rows, n = [], 0

    def add(ts, typ, amt, cat, cur="USD", status="completed"):
        nonlocal n
        n += 1
        rows.append({"transaction_id": f"T{n:04d}", "account_id": "A", "transaction_type": typ, "amount": f"{amt:.2f}",
                     "currency": cur, "merchant_category": cat, "transaction_timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                     "status": status})
    for m in range(1, 7):                                      # rent 1000.00 on the 1st, Jan..Jun 2026
        add(datetime(2026, m, 1, 9), "debit", 1000.00, "housing")
        add(datetime(2026, m, 25, 9), "deposit", 2500.00, "income")        # recorded inflow
    for w in range(8):                               # coffee 4.50 / 4.60 weekly: 8 x 4.50 + 4 x 0.10 = 36.40
        add(datetime(2026, 1, 5, 8) + timedelta(days=7 * w), "debit", 4.50 + (0.1 if w % 2 else 0), "dining")
    add(datetime(2026, 2, 10, 12), "debit", 50.00, "groceries")
    add(datetime(2026, 5, 10, 12), "debit", 300.00, "groceries")              # increase in recent months
    add(datetime(2026, 6, 10, 12), "debit", 200.00, "groceries")
    add(datetime(2026, 6, 11, 12), "refund", 20.00, "groceries")
    add(datetime(2026, 3, 3, 12), "debit", 9999.00, "travel")                 # large isolated
    add(datetime(2026, 4, 3, 12), "debit", 77.00, "retail", status="pending")  # excluded
    add(datetime(2026, 4, 4, 12), "debit", 55.00, "retail", cur="EUR")       # other currency
    return validate_transactions(pl.DataFrame(rows)).clean


@pytest.fixture(scope="module")
def data():
    c = ledger()
    return c, build_summaries(c)


def test_recurring_candidates_find_rent_and_coffee_with_evidence(data):
    c, _ = data
    r = I.recurring_candidates(I.scope(c, "A", "USD"))
    by = {x["merchant_category"]: x for x in r.iter_rows(named=True)}
    assert by["housing"]["period"] == "monthly" and by["housing"]["occurrences"] == 6
    assert by["housing"]["typical_amount_cents"] == 100000 and by["housing"]["confidence"] == "high"
    assert by["dining"]["period"] == "weekly" and by["dining"]["occurrences"] == 8
    assert len(by["housing"]["supporting_transactions"].split(", ")) == 6
    assert "groceries" not in by and "travel" not in by                       # irregular: not candidates


def test_period_spending_excludes_pending_and_other_currency_and_nets_refunds(data):
    c, _ = data
    m = I.period_spending(c, "A", "USD", "month")
    june = m.filter(pl.col("period_start").dt.month() == 6)["spend_cents"][0]
    assert june == 100000 + 20000 - 2000                                     # rent + groceries - refund
    assert m["spend_cents"].sum() == 600000 + 3640 + 5000 + 30000 + 20000 - 2000 + 999900
    w = I.period_spending(c, "A", "USD", "week")
    assert w["spend_cents"].sum() == m["spend_cents"].sum()
    d = I.period_spending(c, "A", "USD", "day")
    assert d["spend_cents"].sum() == m["spend_cents"].sum()


def test_income_is_reported_as_recorded_inflows_not_salary(data):
    c, s = data
    r = I.income_analysis(c, s, "A", "USD")
    assert r["months_with_inflows"] == 6 and r["mean_monthly_cents"] == 250000
    assert "cannot be determined" in r["note"]
    assert r["recurring_candidates"]["period"].to_list() == ["monthly"]


def test_cash_flow_and_ratio(data):
    _, s = data
    cf = I.cash_flow(s, "A", "USD")
    jun = cf.filter(pl.col("month") == "2026-06").row(0, named=True)
    assert jun["income_cents"] == 250000 and jun["expenses_cents"] == 118000
    assert jun["net_cents"] == 132000 and jun["expense_to_income"] == pytest.approx(118000 / 250000)


def test_behaviour_changes_and_large_isolated(data):
    c, s = data
    b = I.behaviour_changes(c, s, "A", "USD")
    inc = {x["category"]: x for x in b["increasing"]}
    assert inc["groceries"]["prior_cents"] == 5000 and inc["groceries"]["recent_cents"] == 48000
    assert b["basis"] == "2026-04..2026-06 vs 2026-01..2026-03"
    assert b["large_isolated"][0]["amount_cents"] == 999900


def test_indicators_are_transparent_and_have_no_aggregate_score(data):
    c, s = data
    ind = I.indicators(c, s, "A", "USD", budgets={"housing": 100000, "groceries": 10000})
    names = [x["indicator"] for x in ind]
    assert not any("score" in n.lower() for n in names)
    assert all(x["formula"] and x["reading"] for x in ind)
    adh = next(x for x in ind if x["indicator"].startswith("Budget adherence"))
    assert adh["value"] == 0.5                                     # housing within, groceries (180 > 100) over
    burden = next(x for x in ind if x["indicator"] == "Recurring payment burden")
    assert isinstance(burden["value"], float) and burden["value"] > 0
