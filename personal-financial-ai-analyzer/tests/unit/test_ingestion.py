"""CSV ingestion & mapping (HW1 F1/P1, HW2 Table 10.1): every bad file -> controlled IngestionError."""
from __future__ import annotations

import polars as pl
import pytest

from src.data import ingestion
from src.data.ingestion import IngestionError, apply_mapping, categorize, ingest, read_csv_bytes, suggest_mapping

BANK_CSV = b"""Date,Description,Amount,Currency
2026-01-03,SUPERMARKET MIGROS,-45.10,USD
2026-01-04,Salary ACME,2000.00,USD
2026-01-05,Coffee corner,-3.50,USD
2026-01-06,Mystery shop 42,-10.00,EUR
"""


@pytest.mark.parametrize("data,msg", [
    (b"", "empty"), (b"   \n ", "empty"), (b"a,b,c\n", "no rows"),
    (b'a,b\n1,"unterminated\n', "could not be read"),
])
def test_bad_files_are_controlled_errors(data, msg):
    with pytest.raises(IngestionError, match=msg):
        read_csv_bytes(data)


def test_too_large_file_rejected_with_size_message(monkeypatch):
    monkeypatch.setattr(ingestion, "MAX_UPLOAD_BYTES", 100)
    with pytest.raises(IngestionError, match="limit"):
        read_csv_bytes(b"x" * 200)


def test_missing_required_column_asks_for_mapping():
    df = read_csv_bytes(b"when,what\n2026-01-01,1\n")
    with pytest.raises(IngestionError, match="Map these required columns"):
        apply_mapping(df, suggest_mapping(df.columns), assume_completed=True)


def test_no_status_requires_explicit_confirmation():
    df = read_csv_bytes(BANK_CSV)
    with pytest.raises(IngestionError, match="no status column"):
        apply_mapping(df, suggest_mapping(df.columns))


def test_bank_style_signed_csv_is_mapped_and_validated():
    res, mapping = ingest(BANK_CSV, assume_completed=True)
    assert mapping["transaction_timestamp"] == "Date" and mapping["amount"] == "Amount"
    c = res.clean.sort("transaction_timestamp")
    assert res.rejected.is_empty()
    assert c["transaction_type"].to_list() == ["debit", "credit", "debit", "debit"]
    assert c["amount_cents"].to_list() == [4510, 200000, 350, 1000]
    assert c["merchant_category"].to_list() == ["groceries", "Uncategorized", "dining", "retail"]
    assert c["transaction_id"].n_unique() == 4
    assert set(c["currency"]) == {"USD", "EUR"}


def test_ids_are_deterministic_across_reuploads():
    a, _ = ingest(BANK_CSV, assume_completed=True)
    b, _ = ingest(BANK_CSV, assume_completed=True)
    assert a.clean["transaction_id"].to_list() == b.clean["transaction_id"].to_list()


def test_invalid_rows_reported_not_crashing():
    data = b"Date,Amount,Currency\n2026-01-01,-5,USD\nnot-a-date,-5,USD\n2026-01-02,abc,USD\n2026-01-03,-1,XXX\n"
    res, _ = ingest(data, assume_completed=True)
    assert res.clean.height == 1
    assert res.reason_counts == {"invalid_amount": 1, "invalid_timestamp": 1, "unknown_currency": 1}


def test_keyword_rules_and_fallback():
    assert categorize("Netflix monthly") == "subscription"
    assert categorize("ATM withdrawal") == "cash"
    assert categorize("xyz") == "Uncategorized"
    assert categorize(None) == "Uncategorized"


def test_mapping_suggestion_is_case_insensitive():
    m = suggest_mapping(["DATE", "amount", "CCY", "Category"])
    assert m["transaction_timestamp"] == "DATE" and m["currency"] == "CCY" and m["merchant_category"] == "Category"


def test_canonical_dataset_columns_map_one_to_one():
    cols = ["transaction_id", "account_id", "transaction_type", "amount", "currency", "merchant_category",
            "balance_after", "transaction_timestamp", "status"]
    m = suggest_mapping(cols)
    assert all(m[c] == c for c in cols if c != "balance_after")
    assert isinstance(apply_mapping(pl.DataFrame({c: ["1"] for c in cols}), m), pl.DataFrame)


def test_iso_t_separator_accepted_and_offsets_rejected_not_shifted():
    """Audit A-05: ISO 'T' timestamps are accepted; timezone offsets are rejected, never silently shifted."""
    data = (b"Date,Amount,Currency\n2026-01-05T10:00:00,-5,USD\n2026-01-06 11:30:00,-6,USD\n"
            b"2026-01-07T09:00:00+03:00,-7,USD\n")
    res, _ = ingest(data, assume_completed=True)
    ts = res.clean.sort("transaction_timestamp")["transaction_timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S").to_list()
    assert ts == ["2026-01-05 10:00:00", "2026-01-06 11:30:00"]
    assert res.reason_counts == {"invalid_timestamp": 1}


def test_file_whose_totals_would_overflow_is_refused_not_wrapped():
    """Master audit M-02: Polars int64 sums wrap silently; 100,000 rows at the per-row bound summed to a
    negative total. Such a file must be refused with a controlled error instead of producing wrong totals."""
    rows = "\n".join(f"2026-01-{(i % 28) + 1:02d},-999999999999.99,USD" for i in range(100_000))
    with pytest.raises(IngestionError, match="supported range"):
        ingest(("Date,Amount,Currency\n" + rows + "\n").encode(), assume_completed=True)


def test_large_but_safe_file_totals_stay_exact():
    rows = "\n".join(f"2026-01-{(i % 28) + 1:02d},-999999999999.99,USD" for i in range(1_000))
    res, _ = ingest(("Date,Amount,Currency\n" + rows + "\n").encode(), assume_completed=True)
    assert res.clean["amount_cents"].sum() == 1_000 * 99_999_999_999_999


@pytest.mark.parametrize("sep", [",", ";", "\t", "|"])
def test_delimiter_is_detected(sep):
    """Master audit 5.1: European (semicolon), tab and pipe exports read correctly, not as one column."""
    data = sep.join(["Date", "Amount", "Currency"]).encode() + b"\n" + sep.join(["2026-01-05", "-12.50", "EUR"]).encode() + b"\n"
    df = ingestion.read_csv_bytes(data)
    assert df.columns == ["Date", "Amount", "Currency"] and df["Amount"].to_list() == ["-12.50"]


def test_encodings_and_bom_are_handled():
    text = "Date,Amount,Currency,Category\n2026-01-05,-3.20,EUR,Café\n"
    assert ingestion.detect_format(text.encode("cp1252"))["encoding"] == "cp1252"
    assert ingestion.read_csv_bytes(text.encode("cp1252"))["Category"].to_list() == ["Café"]
    bom = ingestion.read_csv_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    assert bom.columns[0] == "Date" and ingestion.detect_format(text.encode("utf-8"))["encoding"] == "utf-8"
