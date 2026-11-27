"""E3 anomaly experiment (HW2 5.5, 8.4, 10.3).

* History = completed spending records of the selected accounts in train+validation months.
* Scored = completed spending records in test months (clean copy kept; injections on copies).
* For every (rate, seed): inject, build features from HISTORY statistics only, score with
  robust z-score, per-account Isolation Forest, and global Isolation Forest.
* Per-account forests are fitted once per account (on history only, independent of injections) and
  score every variant's rows of that account; they are discarded afterwards (memory bound).
"""
from __future__ import annotations

import time

import numpy as np
import polars as pl

from src.evaluation.anomaly_metrics import evaluate
from src.experiments.data_splitting import period_expr
from src.features.account_features import FEATURES, build_features, history_stats, spending
from src.models.anomaly.isolation_forest import fit_global, score_per_account
from src.models.anomaly.robust_zscore import robust_z_expr
from src.models.anomaly.synthetic_injection import inject

MODELS = ["robust_zscore", "isolation_forest_per_account", "isolation_forest_global"]


def prepare(tx: pl.DataFrame):
    sp = spending(tx).with_columns(period_expr("month").alias("period"))
    hist = sp.filter(pl.col("period").is_in(["train", "validation"]))
    scored = sp.filter(pl.col("period") == "test")
    acc, cat = history_stats(hist)
    categories = sorted(tx["merchant_category"].unique().to_list())
    return hist, scored, acc, cat, categories


def run(tx: pl.DataFrame, rates: list[float], seeds: list[int], if_cfg: dict, model_seed: int = 42) -> dict:
    t0 = time.time()
    hist, scored, acc, cat, categories = prepare(tx)
    hist_f = build_features(hist, acc, cat)
    variants = {("clean", 0): (scored, pl.DataFrame({"transaction_id": [], "scenario": []},
                                                     schema={"transaction_id": pl.String, "scenario": pl.String}))}
    for r in rates:
        for s in seeds:
            variants[(r, s)] = inject(scored, hist, categories, r, s)

    frames = []
    for vid, (key, (rows, labels)) in enumerate(variants.items()):
        f = (build_features(rows, acc, cat).with_columns(robust_z_expr())
               .join(labels.select("transaction_id", "scenario"), on="transaction_id", how="left")
               .with_columns(pl.lit(vid).alias("variant"), pl.col("scenario").is_not_null().cast(pl.Int8).alias("y")))
        frames.append(f)
    allf = pl.concat(frames, how="diagonal_relaxed").with_row_index("_r")

    # global IF (saved artifact candidate)
    g = fit_global(hist_f.select(FEATURES).to_numpy(), if_cfg, model_seed)
    allf = allf.with_columns(pl.Series("score_if_global", -g.score_samples(allf.select(FEATURES).to_numpy())))

    # per-account IF: fit on history once, score all variants of that account
    hist_by = {a: d.select(FEATURES).to_numpy() for (a,), d in hist_f.group_by("account_id")}
    groups, index = [], {}
    for (a,), d in allf.group_by("account_id"):
        groups.append((a, hist_by.get(a, np.empty((0, len(FEATURES)))), d.select(FEATURES).to_numpy()))
        index[a] = d["_r"].to_numpy()
    scores = score_per_account(groups, if_cfg, model_seed)
    per = np.zeros(allf.height)
    no_model_rows = 0
    for a, (s, fitted) in scores.items():
        per[index[a]] = s
        no_model_rows += 0 if fitted else len(s)
    allf = allf.with_columns(pl.Series("score_if_per_account", per))

    results = []
    col = {"robust_zscore": "score_robust_z", "isolation_forest_per_account": "score_if_per_account",
           "isolation_forest_global": "score_if_global"}
    for vid, key in enumerate(variants):
        if key[0] == "clean":
            continue
        d = allf.filter(pl.col("variant") == vid)
        y = d["y"].to_numpy()
        scen = d["scenario"].fill_null("none").to_numpy()
        for m in MODELS:
            results.append({"rate": key[0], "seed": key[1], "model": m,
                            **evaluate(y, d[col[m]].to_numpy(), scen)})
    return {"results": results, "scores": allf, "variants": variants, "global_model": g,
            "history_rows": hist.height, "scored_rows": scored.height,
            "accounts_without_history_rows": no_model_rows, "seconds": round(time.time() - t0, 1)}
