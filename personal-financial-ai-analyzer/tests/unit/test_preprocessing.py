"""Partition preprocessing (Gate 4): row accounting, period labels, activity counts."""
from __future__ import annotations

from pathlib import Path

import polars as pl

from src.data.preprocessing import process_partition

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def test_every_row_accounted_and_periods_labelled():
    raw = pl.read_csv(FIX / "sample_transactions.csv", infer_schema=False)
    bad = pl.read_csv(FIX / "invalid_rows.csv", infer_schema=False).with_columns(pl.lit(None, dtype=pl.String)
                                                                                  .alias("balance_after"))
    o = process_partition(pl.concat([raw, bad.select(raw.columns)]))
    assert o.validation.clean.height + o.validation.rejected.height == raw.height + bad.height
    assert o.validation.reason_counts == {"invalid_amount": 1, "invalid_timestamp": 1}
    assert set(o.monthly["period"]) == {"validation"}          # 2026-01/02 fall in validation


def test_activity_counts_spending_months_only():
    raw = pl.read_csv(FIX / "sample_transactions.csv", infer_schema=False)
    s = process_partition(raw).series_stats.sort("account_id", "currency")
    got = {(r["account_id"], r["currency"]): r["validation_active_months"] for r in s.iter_rows(named=True)}
    # A1/USD has spending in 2026-01 and 2026-02; A1/EUR only 2026-01; A2/USD 2026-01 (reversed row ignored)
    assert got == {("A1", "EUR"): 1, ("A1", "USD"): 2, ("A2", "USD"): 1}
