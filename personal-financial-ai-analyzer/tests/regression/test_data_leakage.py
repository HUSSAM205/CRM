"""Leakage regression tests (docs/leakage_analysis.md L1-L12). Data-dependent tests skip if the
processed data is not present (fresh clone without the dataset)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from src.experiments.data_splitting import TEST_MONTHS, TRAIN_MONTHS
from src.features.account_features import FEATURES as ANOMALY_FEATURES
from src.features.temporal_features import BASE_FEATURES, SEASONAL_FEATURES

ROOT = Path(__file__).resolve().parents[2]
SPLITS = ROOT / "data/processed/splits"
REG = ROOT / "artifacts/metadata/model_registry.json"
FORBIDDEN = {"balance_after", "account_id", "transaction_id"}


def test_L1_L7_forbidden_columns_absent_from_feature_definitions():
    for feats in (BASE_FEATURES, SEASONAL_FEATURES, ANOMALY_FEATURES):
        assert not FORBIDDEN & set(feats)


@pytest.mark.skipif(not REG.exists(), reason="no trained artifacts")
def test_L1_L7_saved_feature_schemas_exclude_forbidden_columns():
    reg = json.loads(REG.read_text(encoding="utf-8"))
    for kind in reg.values():
        for entry in kind.values():
            fs = ROOT / entry["current"] / "feature_schema.json"
            if fs.exists():
                assert not FORBIDDEN & set(json.loads(fs.read_text(encoding="utf-8"))["features"])


@pytest.mark.skipif(not (SPLITS / "eligible_series.parquet").exists(), reason="splits not built")
def test_L3_eligibility_uses_training_months_only():
    e = pl.read_parquet(SPLITS / "eligible_series.parquet")
    assert (e["train_active_months"] >= 12).all()
    assert e["train_active_months"].max() <= len(TRAIN_MONTHS)
    meta = json.loads((SPLITS / "split_metadata.json").read_text(encoding="utf-8"))
    assert meta["eligible_series"] == e.height == 106_945      # equals the independent read-only count


@pytest.mark.skipif(not (SPLITS / "split_metadata.json").exists(), reason="splits not built")
def test_L11_account_disjoint_panel_shares_no_accounts():
    a = set(pl.read_parquet(SPLITS / "keys_primary.parquet")["account_id"])
    b = set(pl.read_parquet(SPLITS / "keys_disjoint.parquet")["account_id"])
    assert not a & b


INJ = ROOT / "reports/experiments/anomaly/injections"


@pytest.mark.skipif(not (INJ.exists() and (SPLITS / "anomaly_transactions.parquet").exists()),
                    reason="anomaly experiment outputs or derived data not present (fresh clone)")
def test_L10_injected_records_are_test_period_only_and_never_in_history():
    from src.experiments.anomaly_experiment import prepare
    tx = pl.read_parquet(SPLITS / "anomaly_transactions.parquet")
    hist, scored, *_ = prepare(tx)
    hist_ids, test_ids = set(hist["transaction_id"]), set(scored["transaction_id"])
    for f in INJ.glob("*.parquet"):
        ids = set(pl.read_parquet(f)["transaction_id"])
        assert ids <= test_ids and not ids & hist_ids
    months = set(scored["month"])
    assert months <= set(TEST_MONTHS)
    assert hist["month"].max() < TEST_MONTHS[0]


def test_L2_gbr_training_targets_are_train_period_only():
    from src.experiments import forecasting_experiment as fe
    assert max(range(fe.FIRST_TARGET, fe.N_TRAIN)) == len(TRAIN_MONTHS) - 1
    assert fe.VAL_COLS[0] == len(TRAIN_MONTHS) and fe.TEST_COLS[0] == fe.VAL_COLS[-1] + 1


def test_L8_anomaly_history_stats_ignore_scored_rows():
    from datetime import datetime

    from src.features.account_features import build_features, history_stats
    hist = pl.DataFrame({"account_id": ["A"] * 4, "merchant_category": ["x"] * 4, "amount": [10.0, 20.0, 30.0, 40.0],
                         "transaction_timestamp": [datetime(2025, 1, d) for d in (1, 2, 3, 4)]})
    acc, cat = history_stats(hist)
    s1 = pl.DataFrame({"account_id": ["A"], "merchant_category": ["x"], "amount": [25.0],
                       "transaction_timestamp": [datetime(2026, 6, 1)]})
    f = build_features(s1, acc, cat)
    assert f["log_amount_to_category_median"][0] == pytest.approx(np.log(25 / 25))   # median(10..40)=25


def test_E2B_features_use_only_months_before_the_target():
    """Master audit 2 (Gate C): E2-B rows for target month i must not change when months >= i change."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts/research"))
    import forecast_dataset_b as E
    rng = np.random.default_rng(1)
    months = [f"{2024 + k // 12}-{k % 12 + 1:02d}" for k in range(24)]
    y = rng.gamma(2.0, 500.0, 24)
    base = {r["month"]: r for r in E.rows_from_series(0, months, y)}
    for i in range(12, 24):
        z = y.copy()
        z[i:] = rng.gamma(2.0, 5000.0, 24 - i)              # change the target and everything after it
        r = next(r for r in E.rows_from_series(0, months, z) if r["month"] == months[i])
        feats = [k for k in r if k not in ("user", "month", "y")]
        assert all(r[k] == base[months[i]][k] for k in feats), months[i]
