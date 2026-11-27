"""Anomaly review candidates for the dashboard (HW1 F7; HW2 5.5; DECISIONS D-07, D-18).

* Unit = one account AND one currency (amounts in different currencies are never compared).
* History = completed spending records older than the last `recent_months` months in the data;
  scored = completed spending records in those recent months.
* Scores: robust z-score (computed from the user's own history) and the SAVED global Isolation
  Forest artifact (loaded, never retrained).
* Output is labelled "review candidate"; reasons are factual comparisons with the user's history.
"""
from __future__ import annotations

import json
from functools import lru_cache

import joblib
import polars as pl

from src.features.account_features import FEATURES, build_features, history_stats, spending
from src.models.anomaly.robust_zscore import robust_z_expr
from src.models.forecasting.inference import registry
from src.utils.configuration import PROJECT_ROOT

LABEL = "Anomaly review candidate (not confirmed fraud)"
MIN_HISTORY = 5


@lru_cache(maxsize=1)
def global_forest():
    reg = registry().get("anomaly", {}).get("isolation_forest_global")
    if not reg:
        return None
    return joblib.load(PROJECT_ROOT / reg["current"] / "model.joblib")


def recent_cutoff(months: list[str], recent_months: int) -> str:
    return sorted(months)[-recent_months]


def review_candidates(clean: pl.DataFrame, account: str, currency: str, recent_months: int = 3,
                      top: int = 10) -> dict:
    sp = spending(clean.filter((pl.col("account_id") == account) & (pl.col("currency") == currency)))
    months = sorted(sp["month"].unique().to_list())
    if len(months) <= recent_months:
        return {"ok": False, "message": "Not enough months of history to look for unusual transactions."}
    cut = recent_cutoff(months, recent_months)
    hist, scored = sp.filter(pl.col("month") < cut), sp.filter(pl.col("month") >= cut)
    if hist.height < MIN_HISTORY or scored.is_empty():
        return {"ok": False, "message": f"At least {MIN_HISTORY} earlier spending records are needed."}
    acc, cat = history_stats(hist)
    f = build_features(scored, acc, cat).with_columns(robust_z_expr())
    forest = global_forest()
    if forest is not None:
        f = f.with_columns(pl.Series("score_if_global", -forest.score_samples(f.select(FEATURES).to_numpy())))
    else:
        f = f.with_columns(pl.lit(None, dtype=pl.Float64).alias("score_if_global"))
    hours_seen = set(hist["transaction_timestamp"].dt.hour().to_list())
    f = f.with_columns(
        pl.concat_str([
            pl.when(pl.col("log_amount_to_category_median") > 1.0986)   # > 3x the usual amount
              .then(pl.format("amount {}x the usual for this category",
                              pl.col("log_amount_to_category_median").exp().round(1))).otherwise(None),
            pl.when(pl.col("category_history_share") == 0).then(pl.lit("category not seen before")).otherwise(None),
            pl.when(~pl.col("transaction_timestamp").dt.hour().is_in(list(hours_seen)))
              .then(pl.lit("unusual time of day")).otherwise(None),
        ], separator="; ", ignore_nulls=True).alias("reasons"))
    order = "score_if_global" if forest is not None else "score_robust_z"
    cand = (f.sort(order, descending=True).head(top)
              .select("transaction_id", "transaction_timestamp", "merchant_category", "amount", "reasons",
                      pl.col("score_robust_z").round(2), pl.col("score_if_global").round(3)))
    return {"ok": True, "label": LABEL, "history_records": hist.height, "scored_records": scored.height,
            "window": f"{cut} to {months[-1]}", "ranked_by": order, "candidates": cand}


def model_metrics() -> dict:
    p = PROJECT_ROOT / "reports/experiments/anomaly/summary.json"
    return json.loads(p.read_text()) if p.exists() else {}
