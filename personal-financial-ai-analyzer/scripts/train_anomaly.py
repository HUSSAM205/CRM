"""Gate 8/9: run the E3 anomaly experiment and save versioned artifacts.

Outputs: reports/experiments/anomaly/*, artifacts/anomaly/<model>/<version>/*
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.experiments.anomaly_experiment import MODELS, run  # noqa: E402
from src.features.account_features import FEATURES  # noqa: E402
from src.utils.configuration import load_config  # noqa: E402
from src.utils.reproducibility import fingerprint, new_artifact_dir, register, set_seed  # noqa: E402

OUT = ROOT / "reports/experiments/anomaly"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "injections").mkdir(exist_ok=True)
    exp = load_config("experiments")
    acfg = load_config("anomaly_detection")
    seed = exp["seeds"]["primary"]
    set_seed(seed)
    tx = pl.read_parquet(ROOT / "data/processed/splits/anomaly_transactions.parquet")
    res = run(tx, exp["anomaly"]["injection_rates"], exp["seeds"]["robustness"], acfg["isolation_forest"], seed)
    met = pl.DataFrame(res["results"])
    met.write_csv(OUT / "metrics_all_runs.csv")
    agg_cols = ["precision_at_k", "recall_at_k", "roc_auc", "average_precision", "precision_at_100"]
    (met.group_by("rate", "model").agg(*[pl.col(c).mean().alias(f"{c}_mean") for c in agg_cols],
                                       *[pl.col(c).std().alias(f"{c}_std") for c in agg_cols],
                                       pl.col("positives").mean().alias("positives_mean"))
        .sort("rate", "model").write_csv(OUT / "robustness_by_rate.csv"))
    for (r, s), (_, labels) in res["variants"].items():
        if r != "clean":
            labels.write_parquet(OUT / "injections" / f"labels_rate{r}_seed{s}.parquet")
    # primary run scores (rate 1%, seed 42) for figures / failure analysis
    primary_vid = list(res["variants"]).index((exp["anomaly"]["primary_rate"], seed))
    (res["scores"].filter(pl.col("variant") == primary_vid)
        .select("transaction_id", "account_id", "merchant_category", "amount", "y", "scenario",
                "score_robust_z", "score_if_per_account", "score_if_global", *FEATURES)
        .write_parquet(OUT / "primary_scores.parquet"))
    primary = met.filter((pl.col("rate") == exp["anomaly"]["primary_rate"]) & (pl.col("seed") == seed))
    summary = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "seconds": res["seconds"],
               "accounts": tx["account_id"].n_unique(), "history_rows": res["history_rows"],
               "scored_rows": res["scored_rows"], "accounts_without_history_rows": res["accounts_without_history_rows"],
               "primary_rate": exp["anomaly"]["primary_rate"], "primary_seed": seed,
               "primary": primary.to_dicts(), "fingerprint": fingerprint()}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str))

    # artifacts
    d = new_artifact_dir("anomaly", "isolation_forest_global")
    joblib.dump(res["global_model"], d / "model.joblib")
    (d / "feature_schema.json").write_text(json.dumps({"features": FEATURES, "history": acfg["history"],
                                                        "excluded": ["balance_after", "account_id"]}, indent=2))
    (d / "metrics.json").write_text(json.dumps(
        primary.filter(pl.col("model") == "isolation_forest_global").to_dicts(), indent=2))
    (d / "metadata.json").write_text(json.dumps({"model": "IsolationForest (global, account-relative features)",
        "params": acfg["isolation_forest"], "seed": seed, "training_rows": res["history_rows"],
        "training_accounts": tx["account_id"].n_unique(), "trained_on": "history (2024-01..2026-04) spending records",
        "label": acfg["label"], "fingerprint": fingerprint()}, indent=2, default=str))
    register("anomaly", "isolation_forest_global", d, "deployed (loaded by app)")
    for m in ("robust_zscore", "isolation_forest_per_account"):
        d = new_artifact_dir("anomaly", m)
        (d / "metadata.json").write_text(json.dumps({"model": m, "trainable_artifact": False,
            "reason": "parameter-free (z-score) or fitted per account at scoring time (per-account IF, D-07)",
            "config": acfg.get("robust_zscore") if m == "robust_zscore" else acfg["isolation_forest"],
            "fingerprint": fingerprint()}, indent=2, default=str))
        (d / "metrics.json").write_text(json.dumps(primary.filter(pl.col("model") == m).to_dicts(), indent=2))
        register("anomaly", m, d, "experiment/app-computed")
    print(primary.select("model", "positives", "precision_at_k", "recall_at_k", "roc_auc", "average_precision",
                         *[c for c in primary.columns if c.startswith("recall_at_k_")]))
    print(json.dumps({k: v for k, v in summary.items() if k not in ("primary", "fingerprint")}, indent=2))


if __name__ == "__main__":
    MODELS  # noqa: B018 (imported for documentation of evaluated models)
    main()
