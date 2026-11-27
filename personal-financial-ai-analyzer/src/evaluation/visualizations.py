"""Static figures for the report (matplotlib PNG). Every figure reads saved result files only."""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import polars as pl  # noqa: E402

from src.utils.configuration import PROJECT_ROOT  # noqa: E402

FIG = PROJECT_ROOT / "reports/figures"
EXP = PROJECT_ROOT / "reports/experiments"
COL = {"model": "#3B5998", "baseline": "#8C8C8C", "reference": "#D9A441"}


def _save(fig, name: str) -> str:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=150)
    plt.close(fig)
    return f"reports/figures/{name}"


def forecasting_comparison() -> str:
    d = pl.read_csv(PROJECT_ROOT / "reports/evaluation/forecasting_test_with_reference_predictors.csv").sort("MAE")
    base = {"naive", "seasonal_naive", "moving_average_3"}
    colors = [COL["reference"] if k.startswith("reference") else COL["baseline"] if n in base else COL["model"]
              for k, n in zip(d["kind"], d["name"])]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for a, m in zip(ax, ("MAE", "MASE")):
        a.barh(d["name"], d[m], color=colors)
        a.invert_yaxis()
        a.set_title(f"Test {m} (lower is better)")
    fig.suptitle("Forecasting: HW2 models/baselines (blue/grey) vs post-hoc reference predictors (gold)")
    return _save(fig, "forecasting_test_comparison.png")


def forecasting_per_month() -> str:
    d = pl.read_csv(EXP / "forecasting/rolling_origin_per_month.csv")
    fig, ax = plt.subplots(figsize=(9, 4))
    for m in d["model"].unique().sort():
        x = d.filter(pl.col("model") == m).sort("month")
        ax.plot(x["month"], x["MAE"], marker="o", label=m)
    ax.axvline(3.5, color="k", ls=":", lw=1)
    ax.set_title("Rolling-origin one-month-ahead MAE (validation | test)")
    ax.set_ylabel("MAE (currency units)")
    ax.legend(fontsize=8, ncol=3)
    return _save(fig, "forecasting_rolling_origin_mae.png")


def anomaly_auc_by_scenario() -> str:
    d = pl.read_csv(EXP / "anomaly/metrics_all_runs.csv").filter(pl.col("rate") == 0.01)
    models = d["model"].unique().sort().to_list()
    scen = ["roc_auc_amount", "roc_auc_hour", "roc_auc_category", "roc_auc"]
    fig, ax = plt.subplots(figsize=(9, 4))
    w = 0.25
    for i, m in enumerate(models):
        x = d.filter(pl.col("model") == m)
        ax.bar([j + i * w for j in range(len(scen))], [x[c].mean() for c in scen], w, label=m,
               yerr=[x[c].std() for c in scen], capsize=3)
    ax.axhline(0.5, color="k", ls=":", lw=1)
    ax.set_xticks([j + w for j in range(len(scen))], ["amount x5-10", "unusual hour", "rare category", "all"])
    ax.set_ylabel("ROC-AUC (mean ± sd over 3 seeds, 1% rate)")
    ax.set_title("Anomaly ranking on injected anomalies (0.5 = chance)")
    ax.legend(fontsize=8)
    return _save(fig, "anomaly_auc_by_scenario.png")


def anomaly_positive_control() -> str:
    d = json.loads((PROJECT_ROOT / "reports/evaluation/anomaly_positive_control.json").read_text(encoding="utf-8"))["results"]
    ks = sorted(d, key=lambda k: int(k[1:]))
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.plot([int(k[1:]) for k in ks], [d[k]["roc_auc"] for k in ks], marker="o", label="ROC-AUC")
    ax.plot([int(k[1:]) for k in ks], [d[k]["precision_at_k"] for k in ks], marker="s", label="Precision@k")
    ax.set_xscale("log")
    ax.set_xlabel("amount multiplier (1% of test records)")
    ax.set_title("Robust z-score dose-response (pipeline positive control)")
    ax.legend()
    return _save(fig, "anomaly_positive_control.png")


def data_distributions() -> str:
    a = PROJECT_ROOT / "reports/data_audit"
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    h = pl.read_csv(a / "hour_distribution.csv")
    ax[0].bar(h["hour"], h["rows"] / 1e6)
    ax[0].set_title("Rows per hour of day (millions)")
    c = pl.read_csv(a / "category_distribution.csv").sort("rows")
    ax[1].barh(c["merchant_category"], c["rows"] / 1e6)
    ax[1].set_title("Rows per category (millions)")
    m = pl.read_csv(a / "monthly_coverage.csv")
    ax[2].plot(m["month"], m["rows"] / 1e6, marker=".")
    ax[2].set_title("Rows per month (millions)")
    ax[2].tick_params(axis="x", labelrotation=90, labelsize=6)
    return _save(fig, "data_distributions.png")


def all_figures() -> list[str]:
    return [forecasting_comparison(), forecasting_per_month(), anomaly_auc_by_scenario(),
            anomaly_positive_control(), data_distributions()]
