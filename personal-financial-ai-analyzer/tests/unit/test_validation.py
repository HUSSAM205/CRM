"""Input validation cases from HW2 Table 10.1 (CSV validation tests)."""
from __future__ import annotations

import polars as pl
import pytest

from src.data.validation import validate_transactions

BASE = {"transaction_id": "T1", "account_id": "A", "transaction_type": "debit", "amount": "10.00",
        "currency": "USD", "merchant_category": "groceries",
        "transaction_timestamp": "2026-01-01 10:00:00", "status": "completed"}


def frame(*overrides: dict) -> pl.DataFrame:
    rows = [{**BASE, "transaction_id": f"T{i}", **o} for i, o in enumerate(overrides)]
    return pl.DataFrame(rows, schema={k: pl.String for k in BASE})


def test_valid_row_passes_with_exact_cents():
    r = validate_transactions(frame({"amount": "29.96"}))
    assert r.rejected.is_empty()
    assert r.clean["amount_cents"].to_list() == [2996]
    assert r.clean["month"].to_list() == ["2026-01"]


def test_missing_required_column_raises():
    with pytest.raises(ValueError, match="missing required columns"):
        validate_transactions(frame({}).drop("amount"))


@pytest.mark.parametrize("override,reason", [
    ({"transaction_timestamp": "2026-13-45 99:00:00"}, "invalid_timestamp"),
    ({"transaction_timestamp": "yesterday"}, "invalid_timestamp"),
    ({"amount": "twelve"}, "invalid_amount"),
    ({"amount": "inf"}, "invalid_amount"),
    ({"amount": "-5.00"}, "negative_amount"),
    ({"amount": "1.005"}, "amount_precision"),
    ({"currency": "XYZ"}, "unknown_currency"),
    ({"status": "settled"}, "unknown_status"),
    ({"account_id": ""}, "missing_account_id"),
    ({"amount": None}, "missing_amount"),
])
def test_bad_rows_are_rejected_with_reason_not_dropped(override, reason):
    r = validate_transactions(frame({}, override))
    assert r.clean.height == 1 and r.rejected.height == 1
    assert r.rejected["reject_reason"].to_list() == [reason]
    assert r.rejected["source_row"].to_list() == [1]


def test_duplicate_ids_first_kept_rest_reported():
    df = frame({}, {}, {}).with_columns(pl.lit("SAME").alias("transaction_id"))
    r = validate_transactions(df)
    assert r.clean["source_row"].to_list() == [0]
    assert r.reason_counts == {"duplicate_transaction_id": 2}


def test_same_amount_and_date_distinct_ids_are_kept():
    r = validate_transactions(frame({}, {}))
    assert r.clean.height == 2 and r.rejected.is_empty()


def test_invalid_row_does_not_shadow_a_later_valid_duplicate_id():
    df = frame({"amount": "bad"}, {}).with_columns(pl.lit("SAME").alias("transaction_id"))
    r = validate_transactions(df)
    assert r.clean["source_row"].to_list() == [1]
    assert r.reason_counts == {"invalid_amount": 1}


def test_missing_category_becomes_uncategorized():
    r = validate_transactions(frame({"merchant_category": ""}, {"merchant_category": None}))
    assert r.clean["merchant_category"].to_list() == ["Uncategorized", "Uncategorized"]


def test_every_input_row_accounted_for():
    df = frame({}, {"amount": "x"}, {"currency": "ABC"}, {}, {"status": "?"})
    r = validate_transactions(df)
    assert r.clean.height + r.rejected.height == df.height


def test_fallback_label_is_canonical_whatever_its_source():
    r = validate_transactions(frame({"merchant_category": ""}, {"merchant_category": "uncategorized"},
                                    {"merchant_category": "UNCATEGORIZED"}, {"merchant_category": "Groceries"}))
    assert r.clean["merchant_category"].to_list() == ["Uncategorized"] * 3 + ["groceries"]


def test_huge_amounts_are_rejected_not_crashing():
    """Audit defect A-01: an amount beyond the int64-cents range raised an uncaught exception."""
    r = validate_transactions(frame({"amount": "92233720368547758.07"}, {"amount": "1000000000000.01"},
                                    {"amount": "999999999999.99"}))
    assert r.rejected["reject_reason"].to_list() == ["amount_out_of_range", "amount_out_of_range"]
    assert r.clean["amount_cents"].to_list() == [99999999999999]          # exact at the bound


def test_large_two_decimal_amounts_convert_exactly():
    vals = ["123456789.99", "12345678901.23", "999999999999.99", "0.10", "0.20"]
    r = validate_transactions(frame(*[{"amount": v} for v in vals]))
    from decimal import Decimal
    assert r.clean["amount_cents"].to_list() == [int(Decimal(v) * 100) for v in vals]
