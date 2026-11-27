"""Anomaly review candidates for the dashboard (HW1 F7; HW2 5.5; DECISIONS D-07, D-18).

* Unit = one account AND one currency (amounts in different currencies are never compared).
* History = completed spending records older than the last `recent_months` months in the data;
  scored = completed spending records in those recent months.
* Scores: robust z-score (computed from the user's own history) and the SAVED global Isolation
  Forest artifact (loaded, never retrained).
* Output is labelled "Unusual transaction — review recommended." (never "fraud"). Every alert carries its
  evidence: amount, currency, timestamp, category, the usual amount in the user's own history, the
  detection method, both scores and a plain explanation (master audit 7.12).
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

LABEL = "Unusual transaction — review recommended."
NOT_FRAUD = "This is a statistical comparison with your own history, not a fraud finding."
METHOD = ("Isolation Forest (saved global model) ranks the top 5; transactions that break a clear rule (rare "
          "category, unusual timing, unusual amount) are added; robust z-score shown alongside")
LIMITATIONS = ("On the synthetic benchmark (1% injected anomalies) only about 1 in 24 flagged transactions was a "
               "true injected anomaly; unusual hours and rare categories were not detectable there.")
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
                      top: int = 5) -> dict:
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
        (pl.col("log_amount_to_category_median") > 1.0986).alias("f_amount"),            # > 3x the usual amount
        (pl.col("category_history_share") == 0).alias("f_category"),
        (~pl.col("transaction_timestamp").dt.hour().is_in(list(hours_seen))).alias("f_hour"),
        pl.col("cat_n").is_between(1, 2).alias("f_thin"))
    f = f.with_columns(
        pl.concat_str([
            pl.when(pl.col("f_amount")).then(pl.format("Unusual amount: {}x your usual for this category",
                                                       pl.col("log_amount_to_category_median").exp().round(1))),
            pl.when(pl.col("f_category")).then(pl.lit("Rare category: not seen in your history before")),
            pl.when(pl.col("f_hour")).then(pl.lit("Unusual timing: an hour of day you have not used before")),
            pl.when(pl.col("f_thin")).then(pl.lit("Insufficient historical context: only 1-2 earlier payments "
                                                  "in this category")),
        ], separator="; ", ignore_nulls=True).alias("reasons"),
        (pl.col("f_amount") | pl.col("f_category") | pl.col("f_hour")).alias("rule_hit"))
    order = "score_if_global" if forest is not None else "score_robust_z"
    # Candidates = the `top` highest model scores PLUS up to `top` further rule hits (rare category, unusual
    # timing, unusual amount), so an explained rule hit is never hidden behind the model ranking (master audit
    # 2: Dataset C showed rare-category rows were explained but never surfaced). At most 2 x top rows.
    ranked = f.sort(order, descending=True).with_row_index("_rank")
    extra = ranked.filter((pl.col("_rank") >= top) & pl.col("rule_hit")).head(top)
    chosen = pl.concat([ranked.head(top), extra]).sort("_rank")
    cand = (chosen
              .select("transaction_id", "transaction_timestamp", "merchant_category", "amount",
                      pl.lit(currency).alias("currency"),
                      pl.col("ref_median").round(2).alias("usual_amount_in_your_history"),
                      pl.when(pl.col("reasons").is_null() | (pl.col("reasons") == ""))
                        .then(pl.lit("Unusual combination: amount, time and category together are uncommon for you "
                                     "(no single rule triggered)"))
                        .otherwise(pl.col("reasons")).alias("explanation"),
                      pl.when(pl.col("_rank") < top).then(pl.lit("model score")).otherwise(pl.lit("rule"))
                        .alias("surfaced_by"),
                      pl.col("score_robust_z").round(2), pl.col("score_if_global").round(3)))
    return {"ok": True, "label": LABEL, "not_fraud": NOT_FRAUD, "method": METHOD, "limitations": LIMITATIONS,
            "history_records": hist.height, "scored_records": scored.height,
            "window": f"{cut} to {months[-1]}", "ranked_by": order, "candidates": cand}


def model_metrics() -> dict:
    p = PROJECT_ROOT / "reports/experiments/anomaly/summary.json"
    return json.loads(p.read_text()) if p.exists() else {}
