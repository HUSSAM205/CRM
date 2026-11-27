"""Append/import workflow (master audit 3: MA3-01, MA3-02)."""
from __future__ import annotations

import polars as pl
import pytest

from src.data.ingestion import ingest, suggest_mapping
from src.data.merge import merge
from src.data.validation import TotalOutOfRangeError

HDR = "Date,Amount,Currency,Description\n"
JAN = "2026-01-03,-12.50,USD,coffee shop\n2026-01-05,-40.00,USD,grocery store\n2026-01-31,1500.00,USD,salary\n"
FEB = "2026-02-02,-9.99,USD,netflix\n2026-02-03,-12.50,USD,coffee shop\n"


def _load(text: str):
    data = (HDR + text).encode()
    res, _ = ingest(data, suggest_mapping(["Date", "Amount", "Currency", "Description"]), assume_completed=True)
    return res


def test_generated_ids_do_not_depend_on_row_position():
    """MA3-02: the same transaction gets the same ID in two exports even when it sits on another line."""
    a = _load(JAN)
    b = _load("2026-01-31,1500.00,USD,salary\n2026-01-03,-12.50,USD,coffee shop\n")
    ida = dict(zip(a.clean["amount"], a.clean["transaction_id"]))
    idb = dict(zip(b.clean["amount"], b.clean["transaction_id"]))
    assert ida[12.5] == idb[12.5] and ida[1500.0] == idb[1500.0]


def test_identical_purchases_in_one_file_stay_distinct():
    r = _load("2026-01-03,-3.00,USD,coffee\n2026-01-03,-3.00,USD,coffee\n")
    assert r.clean.height == 2 and r.clean["transaction_id"].n_unique() == 2 and r.rejected.height == 0


def test_overlapping_export_adds_only_new_records_and_keeps_existing():
    first, second = _load(JAN), _load(JAN.splitlines(True)[2] + FEB)     # overlap: the salary row
    m = merge(first.clean, first.rejected, "jan.csv", second.clean, second.rejected, "feb.csv")
    assert m.added == 2 and m.already_loaded == 1
    assert m.clean.height == 5                                          # 3 existing + 2 new, none dropped
    assert set(first.clean["transaction_id"]) <= set(m.clean["transaction_id"])
    skipped = m.rejected.filter(pl.col("reject_reason") == "already_loaded")
    assert skipped.height == 1 and skipped["source_file"][0] == "feb.csv"
    assert skipped["amount"][0] == "1500.0"
    # every input row is accounted for exactly once: clean or rejected
    assert m.clean.height + m.rejected.height == first.clean.height + second.clean.height


def test_reimporting_the_same_records_adds_nothing():
    a = _load(JAN)
    m = merge(a.clean, a.rejected, "x", _load(JAN).clean, _load(JAN).rejected, "x again")
    assert m.added == 0 and m.already_loaded == 3 and m.clean.height == 3


def test_same_id_in_another_account_is_not_a_duplicate():
    a = pl.DataFrame({"account_id": ["A"], "transaction_id": ["t1"]})
    b = pl.DataFrame({"account_id": ["B"], "transaction_id": ["t1"]})
    full = _load(JAN).clean.head(1)
    ca = full.with_columns(pl.lit("A").alias("account_id"), pl.lit("t1").alias("transaction_id"))
    cb = full.with_columns(pl.lit("B").alias("account_id"), pl.lit("t1").alias("transaction_id"))
    rej = _load(JAN).rejected
    m = merge(ca, rej, "a", cb, rej, "b")
    assert m.added == 1 and m.already_loaded == 0 and a.height == b.height == 1


def test_combined_total_range_is_rechecked():
    big = "".join(f"2026-01-{(i % 28) + 1:02d},-999999999999.99,USD,x{i}\n" for i in range(30000))   # 3.0e16 per file < limit (4.6e16) < 6.0e16 combined
    a, b = _load(big), _load(big.replace(",x", ",y"))
    with pytest.raises(TotalOutOfRangeError, match="combined"):
        merge(a.clean, a.rejected, "a", b.clean, b.rejected, "b")
