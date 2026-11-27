"""Anomaly components: injection, features (history-only), robust z, metrics, determinism."""
from __future__ import annotations

from datetime import datetime

import numpy as np
import polars as pl
import pytest

from src.evaluation.anomaly_metrics import evaluate, precision_recall_at_k
from src.features.account_features import FEATURES, build_features, history_stats
from src.models.anomaly.isolation_forest import fit_global, score_per_account
from src.models.anomaly.robust_zscore import robust_z_expr
from src.models.anomaly.synthetic_injection import inject

CATS = ["dining", "groceries", "travel"]


def frame(n: int, acc: str = "A", seed: int = 0, month: int = 1) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    return pl.DataFrame({
        "transaction_id": [f"{acc}{month}-{i}" for i in range(n)], "account_id": [acc] * n,
        "transaction_type": ["debit"] * n, "status": ["completed"] * n,
        "amount": np.round(rng.uniform(10, 20, n), 2), "merchant_category": ["groceries"] * (n - 2) + ["dining"] * 2,
        "transaction_timestamp": [datetime(2025, month, 1 + i % 27, 9 + i % 3) for i in range(n)]})


def test_injection_modifies_copy_and_records_labels():
    hist, scored = frame(40), frame(200, seed=1, month=6)
    mod, labels = inject(scored, hist, CATS, rate=0.05, seed=42)
    assert labels.height == 10 and scored.equals(frame(200, seed=1, month=6))   # clean preserved
    lab = labels.join(mod, on="transaction_id")
    for r in lab.iter_rows(named=True):
        if r["scenario"] == "amount":
            assert 5 <= r["amount"] / r["original_amount"] <= 10.01
        elif r["scenario"] == "hour":
            assert r["transaction_timestamp"].hour not in {9, 10, 11}               # never seen in history
        else:
            assert r["merchant_category"] == "travel"                             # least used (never seen)
    assert mod.filter(~pl.col("transaction_id").is_in(labels["transaction_id"].implode())).equals(
        scored.filter(~pl.col("transaction_id").is_in(labels["transaction_id"].implode())))


def test_injection_is_seeded():
    hist, scored = frame(40), frame(200, seed=1, month=6)
    a = inject(scored, hist, CATS, 0.02, 7)[1]
    b = inject(scored, hist, CATS, 0.02, 7)[1]
    c = inject(scored, hist, CATS, 0.02, 8)[1]
    assert a.equals(b) and not a.equals(c)


def test_features_use_history_statistics_only():
    hist, scored = frame(40), frame(20, seed=1, month=6)
    acc, cat = history_stats(hist)
    f1 = build_features(scored, acc, cat)
    huge = scored.with_columns(pl.col("amount") * 1000)        # changing scored rows must not move stats
    f2 = build_features(huge, acc, cat)
    assert f1["category_history_share"].equals(f2["category_history_share"])
    assert (f2["log_amount_to_category_median"] - f1["log_amount_to_category_median"]).abs().min() > 6.9


def test_robust_z_hand_value():
    df = pl.DataFrame({"amount": [np.e ** 2], "acc_log_median": [1.0], "acc_log_mad": [0.5]})
    assert df.select(robust_z_expr()).item() == pytest.approx(0.6745 * 1 / 0.5)


def test_metrics_hand_values():
    y = np.array([1, 0, 1, 0, 0])
    s = np.array([0.9, 0.8, 0.1, 0.2, 0.3])
    assert precision_recall_at_k(y, s, 2) == (0.5, 0.5)
    assert evaluate(y, s)["roc_auc"] == pytest.approx(3 / 6)


def test_isolation_forest_scores_are_deterministic_and_rank_outlier_first():
    hist = frame(60)
    acc, cat = history_stats(hist)
    hf = build_features(hist, acc, cat).select(FEATURES).to_numpy()
    probe = frame(5, seed=3, month=6).with_columns(
        pl.when(pl.int_range(pl.len()) == 0).then(pl.col("amount") * 50).otherwise(pl.col("amount")).alias("amount"))
    pf = build_features(probe, acc, cat).select(FEATURES).to_numpy()
    cfg = {"n_estimators": 100, "max_samples": "auto", "contamination": "auto"}
    s1 = score_per_account([("A", hf, pf)], cfg, 42, n_jobs=1)["A"][0]
    s2 = score_per_account([("A", hf, pf)], cfg, 42, n_jobs=1)["A"][0]
    assert np.array_equal(s1, s2)                              # score consistency (same seed)
    # Isolation Forest cannot extrapolate: a value beyond the training range is isolated no faster than
    # the most extreme TRAINING point, so it is not guaranteed to rank above rare in-range patterns
    # (rows 3-4 are the rarely used 'dining' category). The guaranteed property: the extreme row ranks
    # above the typical rows (1-2: common category, normal amount).
    assert s1[0] > s1[1] and s1[0] > s1[2]
    g = fit_global(hf, cfg, 42)
    gs = -g.score_samples(pf)
    assert gs[0] > gs[1] and gs[0] > gs[2]


def test_injection_keeps_amount_cents_consistent_when_present():
    hist = frame(40)
    scored = frame(100, seed=1, month=6).with_columns((pl.col("amount") * 100).round(0).cast(pl.Int64).alias("amount_cents"))
    mod, labels = inject(scored, hist, CATS, rate=0.1, seed=1)
    assert mod.columns == scored.columns
    assert (mod["amount_cents"] == (mod["amount"] * 100).round(0).cast(pl.Int64)).all()


def test_hour_injection_when_least_used_hour_is_the_current_one():
    # history uses every hour 0..23 twice except hour 9 (used once); the scored record is AT hour 9.
    hours = [h for h in range(24) for _ in range(2) if h != 9] + [9]
    hist = pl.DataFrame({"transaction_id": [f"h{i}" for i in range(len(hours))], "account_id": ["A"] * len(hours),
                         "amount": [10.0] * len(hours), "merchant_category": ["groceries"] * len(hours),
                         "transaction_timestamp": [datetime(2025, 1, 1, h) for h in hours]})
    scored = pl.DataFrame({"transaction_id": ["s0"], "account_id": ["A"], "amount": [10.0],
                           "merchant_category": ["groceries"], "transaction_timestamp": [datetime(2026, 6, 1, 9)]})
    for seed in range(30):   # whichever scenario is drawn, injection must not fail
        mod, labels = inject(scored, hist, CATS, rate=1.0, seed=seed)
        if labels["scenario"][0] == "hour":
            assert mod["transaction_timestamp"][0].hour != 9
