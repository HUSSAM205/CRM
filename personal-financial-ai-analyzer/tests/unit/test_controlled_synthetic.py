"""Dataset C (controlled synthetic, known ground truth): generator determinism, exact financials, rule-hit
surfacing with standard labels (master audit 2)."""
from __future__ import annotations

import sys
from pathlib import Path

import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/research"))
import controlled_synthetic as C  # noqa: E402

from src.analytics.aggregation import build_summaries  # noqa: E402
from src.data.validation import validate_transactions  # noqa: E402


@pytest.fixture(scope="module")
def small():
    raw, truth = C.generate(seed=7, n_users=8)
    v = validate_transactions(raw)
    return raw, truth, v, build_summaries(v.clean)


def test_generator_is_deterministic():
    a, ta = C.generate(seed=7, n_users=4)
    b, tb = C.generate(seed=7, n_users=4)
    assert a.equals(b) and ta == tb


def test_controlled_ledger_totals_are_exact_incl_try_refunds_transfers_pending(small):
    raw, _, v, s = small
    assert v.rejected.is_empty() and "TRY" in set(v.clean["currency"])
    r = C.c1_financial(raw, v.clean, s)
    assert r["mismatches"] == 0 and r["checks"] > 0


def test_rule_hits_are_surfaced_with_standard_labels(small):
    from src.models.anomaly.anomaly_scoring import review_candidates
    _, truth, v, _ = small
    cat = next(a for a in truth["anomalies"] if a["type"] == "category")
    cur = v.clean.filter(pl.col("account_id") == cat["user"])["currency"][0]
    r = review_candidates(v.clean, cat["user"], cur)
    row = r["candidates"].filter(pl.col("transaction_id") == cat["transaction_id"])
    assert row.height == 1 and "Rare category" in row["explanation"][0]
    assert r["candidates"].height <= 10 and set(r["candidates"]["surfaced_by"]) <= {"model score", "rule"}
