"""Budget suggestions and alerts (HW2 5.6) against hand-calculated values."""
from __future__ import annotations

import polars as pl

from src.budget.budget_alerts import budget_status
from src.budget.budget_calculator import previous_months, suggest_budgets


def cat_frame() -> pl.DataFrame:
    rows = []
    for cat, vals in {"groceries": [10000, 30000, 20000, 17000], "dining": [5000, 7000, 6000, 7000],
                      "travel": [0, 0, 90000, 0]}.items():
        for m, v in zip(["2026-01", "2026-02", "2026-03", "2026-04"], vals):
            if v:
                rows.append({"account_id": "A", "currency": "USD", "month": m, "merchant_category": cat,
                             "gross_spending_cents": v, "refund_cents": 0, "net_spending_cents": v})
    return pl.DataFrame(rows)


def test_previous_months_crosses_year():
    assert previous_months("2026-02", 3) == ["2025-11", "2025-12", "2026-01"]


def test_median_of_last_three_completed_months():
    b = {r["merchant_category"]: r for r in suggest_budgets(cat_frame(), "A", "USD", "2026-04").iter_rows(named=True)}
    assert b["groceries"]["suggested_cents"] == 20000           # median(100, 300, 200)
    assert b["dining"]["suggested_cents"] == 6000               # median(50, 70, 60)
    assert b["travel"]["suggested_cents"] == 0                  # median(0, 0, 900): missing months count as 0
    assert b["groceries"]["spent_current_cents"] == 17000
    assert "Median of 2026-01, 2026-02, 2026-03" in b["groceries"]["explanation"]


def test_alert_thresholds():
    assert budget_status(7999, 10000)["level"] == "ok"
    assert budget_status(8000, 10000)["level"] == "warning"      # exactly 80%
    assert budget_status(10000, 10000)["level"] == "exceeded"    # exactly 100%
    assert budget_status(500, 0)["level"] == "no_budget"
    assert budget_status(-100, 1000)["level"] == "ok"            # refunds exceeded spending
