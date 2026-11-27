"""Summary objects, period totals, month comparison and category distribution (hand values)."""
from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from src.analytics.aggregation import build_summaries, period_totals
from src.analytics.category_analysis import category_distribution
from src.analytics.monthly_analysis import compare_months
from src.data.validation import validate_transactions

FIX = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture(scope="module")
def s():
    return build_summaries(validate_transactions(pl.read_csv(FIX / "sample_transactions.csv", infer_schema=False)).clean)


def test_summary_metadata(s):
    assert s.accounts == ["A1", "A2"] and s.currencies == ["EUR", "USD"]
    assert s.months("A1", "USD") == ["2026-01", "2026-02"]


def test_period_totals_sum_months(s):
    t = period_totals(s, "A1", "USD")
    assert t["expenses_cents"] == 13275 + 20031 and t["income_cents"] == 100115 + 50000
    assert t["excluded_status_records"] == 3


def test_compare_months_hand_values(s):
    c = {r["merchant_category"]: r for r in compare_months(s.category, "A1", "USD", "2026-01", "2026-02").iter_rows(named=True)}
    assert c["groceries"]["change_cents"] == 3030 - 8000
    assert c["dining"]["change_cents"] == -2999 - 5025
    assert c["cash"]["2026-01_cents"] == 0 and c["cash"]["change_cents"] == 20000


def test_category_distribution_shares(s):
    d = category_distribution(s.category, "A1", "USD", "2026-01", "2026-02")
    by = dict(zip(d["merchant_category"], d["net_spending_cents"]))
    assert by == {"cash": 20000, "groceries": 11030, "dining": 2026}
    assert d["share_of_spending"].sum() == pytest.approx(1.0)
