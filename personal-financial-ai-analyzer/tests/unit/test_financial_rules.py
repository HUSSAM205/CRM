"""Financial correctness against independently hand-calculated results (HW2 E1, 10.2)."""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest

from src.analytics.financial_metrics import category_spending, monthly_summary, summarize
from src.data.validation import validate_transactions
from src.rules.currency_rules import MixedCurrencyError, single_currency
from src.rules.transaction_mapping import TYPE_MEANING, meaning_of

FIX = Path(__file__).resolve().parents[1] / "fixtures"
EXPECTED = json.loads((FIX / "expected_financial_results.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def clean() -> pl.DataFrame:
    raw = pl.read_csv(FIX / "sample_transactions.csv", infer_schema=False)
    res = validate_transactions(raw)
    assert res.rejected.is_empty(), res.rejected
    return res.clean


def _strip(rows):
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]


def test_monthly_summary_matches_hand_calculation(clean):
    got = monthly_summary(clean).drop("unresolved_type_records").to_dicts()
    exp = _strip(EXPECTED["monthly_summary"])
    assert len(got) == len(exp)
    for g, e in zip(got, exp):
        for k, v in e.items():
            assert g[k] == v, (k, g, e)


def test_category_spending_matches_hand_calculation(clean):
    assert category_spending(clean).to_dicts() == EXPECTED["category_spending"]


def test_category_plus_fees_equals_expenses(clean):
    m = monthly_summary(clean)
    c = (category_spending(clean).group_by("account_id", "currency", "month")
         .agg(pl.col("net_spending_cents").sum()))
    j = m.join(c, on=["account_id", "currency", "month"], how="left").with_columns(
        pl.col("net_spending_cents").fill_null(0))
    assert (j["net_spending_cents"] + j["fee_cents"] == j["expenses_cents"]).all()


def test_transfers_excluded_from_income_and_expenses(clean):
    row = monthly_summary(clean).filter((pl.col("account_id") == "A1") & (pl.col("currency") == "USD")
                                        & (pl.col("month") == "2026-01")).row(0, named=True)
    assert row["transfer_cents"] == 30000
    assert row["income_cents"] == 100115 and row["expenses_cents"] == 13275


@pytest.mark.parametrize("status", ["pending", "failed", "reversed"])
def test_non_completed_never_counted(clean, status):
    only = clean.filter(pl.col("status") == status)
    assert only.height > 0
    s = summarize(only, ["currency"])
    for col in ["income_cents", "outflow_cents", "fee_cents", "refund_cents", "transfer_cents",
                "expenses_cents", "net_cash_flow_cents", "completed_records"]:
        assert s[col].sum() == 0
    assert s["excluded_status_records"].sum() == only.height


def test_currencies_never_combined(clean):
    with pytest.raises(MixedCurrencyError):
        summarize(clean, ["account_id", "month"])
    with pytest.raises(MixedCurrencyError):
        single_currency(clean)
    usd = monthly_summary(clean, by_account=False).filter(pl.col("currency") == "USD")
    assert set(usd["currency"]) == {"USD"}


def test_unknown_type_is_unresolved_not_guessed():
    assert meaning_of("salary") == "unresolved"
    assert meaning_of(None) == "unresolved"
    df = pl.DataFrame({"transaction_id": ["X1"], "account_id": ["A"], "transaction_type": ["salary"],
                       "amount": ["10.00"], "currency": ["USD"], "merchant_category": ["other"],
                       "transaction_timestamp": ["2026-01-01 00:00:00"], "status": ["completed"]})
    clean = validate_transactions(df).clean
    s = summarize(clean, ["currency"]).row(0, named=True)
    assert s["unresolved_type_records"] == 1
    assert s["income_cents"] == 0 and s["expenses_cents"] == 0


def test_mapping_covers_exactly_the_eight_documented_types():
    assert set(TYPE_MEANING) == {"debit", "credit", "transfer", "fee", "interest", "refund",
                                 "withdrawal", "deposit"}
