"""E3-B: unusual-transaction ranking on Dataset B labels (PersonaLedger identity_theft_1months/test.parquet,
CC BY 4.0, revision c90078ae, SHA-256 d68c03e8...). A SEPARATE experiment; HW2 E3 is unchanged.

Pre-registered protocol (fixed before any result):
  * Each sequence = one user-month in which one day of another user's transactions was injected by the
    dataset authors (`is_fraud` = True). Labels are used ONLY for evaluation.
  * 3,135 of 108,078 sequences have no labels at all (is_fraud null on every row); they are excluded before
    sampling (decided when the nulls were found, before any metric was computed).
  * Sample: 5,000 sequences per run, chosen with a seeded RNG over sorted seq_ids; runs with seeds 42, 43, 44.
  * Scoring is unsupervised and per sequence (the app's unit is one account): statistics come from the
    sequence's own transactions.
  * Features (same five as HW2 / the app): log amount, hour, weekday, merchant-type history share
    (share of the OTHER rows of the sequence with the same merchant type), log(amount / merchant-type median
    in the sequence, fallback sequence median). Feature-engineering variant "+B": adds merchant-name novelty
    (name not seen in the other rows) and card-present flag (fields that Dataset A does not have).
  * Methods: robust z-score of log amount (median/MAD), global Isolation Forest (100 trees, seed = run seed)
    on 5 features, and on 7 features (+B).
  * Metrics: ROC-AUC, average precision, precision/recall/F1 at k = number of positives, FPR at k,
    per-sequence top-1 hit rate (share of sequences whose most unusual row is injected).
Outputs: reports/experiments/anomaly_dataset_b/summary.json and metrics.csv.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/supplementary/personaledger/identity_theft_1months/test.parquet"
OUT = ROOT / "reports/experiments/anomaly_dataset_b"
F5 = ["log_amount", "hour", "weekday", "type_share", "log_amount_to_type_median"]
F7 = F5 + ["name_novel", "card_present"]


def features(d: pl.DataFrame) -> pl.DataFrame:
    d = d.with_columns(pl.col("amount").abs().clip(lower_bound=0.01).alias("a")).with_columns(
        pl.col("a").log().alias("log_amount"), pl.col("timestamp").dt.hour().cast(pl.Float64).alias("hour"),
        pl.col("timestamp").dt.weekday().cast(pl.Float64).alias("weekday"),
        (pl.col("card_present_or_not") == "yes").cast(pl.Float64).alias("card_present"))
    d = d.with_columns(
        ((pl.len().over("seq_id", "merchant_type") - 1) / (pl.len().over("seq_id") - 1)).alias("type_share"),
        (pl.len().over("seq_id", "merchant_name") == 1).cast(pl.Float64).alias("name_novel"),
        pl.col("a").median().over("seq_id", "merchant_type").alias("tmed"), pl.col("a").median().over("seq_id").alias("smed"),
        pl.col("log_amount").median().over("seq_id").alias("lmed"))
    d = d.with_columns(pl.when(pl.len().over("seq_id", "merchant_type") > 1).then(pl.col("tmed")).otherwise(pl.col("smed"))
                         .log().alias("lref"),
                       (pl.col("log_amount") - pl.col("lmed")).abs().median().over("seq_id").alias("mad"))
    return d.with_columns((pl.col("log_amount") - pl.col("lref")).alias("log_amount_to_type_median"),
                          ((pl.col("log_amount") - pl.col("lmed")).abs() / (1.4826 * pl.col("mad") + 1e-9)).alias("z"))


def evaluate(y: np.ndarray, s: np.ndarray, seq: np.ndarray) -> dict:
    k = int(y.sum())
    top = np.argsort(-s)[:k]
    tp = int(y[top].sum())
    df = pl.DataFrame({"seq": seq, "s": s, "y": y})
    top1 = df.sort("s", descending=True).group_by("seq", maintain_order=True).first()
    return {"roc_auc": float(roc_auc_score(y, s)), "average_precision": float(average_precision_score(y, s)),
            "k": k, "precision_at_k": tp / k, "recall_at_k": tp / k, "f1_at_k": tp / k,
            "fpr_at_k": (k - tp) / int((y == 0).sum()), "top1_hit_rate": float(top1["y"].mean())}


def main() -> None:
    t0 = time.time()
    ids = (pl.scan_parquet(SRC).group_by("seq_id").agg(pl.col("is_fraud").null_count().alias("nn"))
             .filter(pl.col("nn") == 0).select(pl.col("seq_id").sort()).collect()["seq_id"].to_numpy())
    runs, rows = [], []
    for seed in (42, 43, 44):
        pick = np.random.default_rng(seed).choice(ids, 5000, replace=False)
        d = features(pl.scan_parquet(SRC).filter(pl.col("seq_id").is_in(pick.tolist())).collect())
        y, seq = d["is_fraud"].to_numpy().astype(int), d["seq_id"].to_numpy()
        res = {"seed": seed, "sequences": 5000, "rows": d.height, "positives": int(y.sum())}
        res["robust_z"] = evaluate(y, d["z"].to_numpy(), seq)
        for name, fs in (("isolation_forest_5f", F5), ("isolation_forest_7f_plusB", F7)):
            X = d.select(fs).to_numpy()
            res[name] = evaluate(y, -IsolationForest(n_estimators=100, random_state=seed).fit(X).score_samples(X), seq)
        runs.append(res)
        for m in ("robust_z", "isolation_forest_5f", "isolation_forest_7f_plusB"):
            rows.append({"seed": seed, "model": m, **res[m]})
    mdf = pl.DataFrame(rows)
    agg = mdf.group_by("model").agg([pl.col(c).mean().alias(f"{c}_mean") for c in
                                     ("roc_auc", "average_precision", "f1_at_k", "fpr_at_k", "top1_hit_rate")] +
                                    [pl.col("roc_auc").std().alias("roc_auc_std")]).sort("model")
    OUT.mkdir(parents=True, exist_ok=True)
    mdf.write_csv(OUT / "metrics.csv")
    summ = {"protocol": __doc__, "runs": runs, "mean_over_seeds": agg.to_dicts(), "seconds": round(time.time() - t0, 1)}
    (OUT / "summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    print(agg)
    print("positives per run", [r["positives"] for r in runs], "rows", [r["rows"] for r in runs], summ["seconds"], "s")


if __name__ == "__main__":
    main()
