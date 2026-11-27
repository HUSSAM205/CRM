"""Master audit 3 (MA3-12): F1 and false-positive rate for HW2 E3, derived READ-ONLY from the saved primary
scores (reports/experiments/anomaly/primary_scores.parquet; 1% injection, seed 42). The experiment, its
scores and its saved summary are not changed. Operating point k = number of injected positives (HW2's
Precision@k), plus the top 1% and top 5% of scored records. FPR = false positives / true negatives + false
positives. Output: reports/master_audit_3/anomaly_derived_metrics.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
SCORES = {"robust_zscore": "score_robust_z", "isolation_forest_per_account": "score_if_per_account",
          "isolation_forest_global": "score_if_global"}


def at_k(y: np.ndarray, s: np.ndarray, k: int) -> dict:
    top = np.zeros_like(y, dtype=bool)
    top[np.argsort(-s, kind="stable")[:k]] = True
    tp, fp = int((top & (y == 1)).sum()), int((top & (y == 0)).sum())
    fn, tn = int(((~top) & (y == 1)).sum()), int(((~top) & (y == 0)).sum())
    p, r = tp / k, tp / (tp + fn)
    return {"k": k, "tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": p, "recall": r,
            "f1": 0.0 if p + r == 0 else 2 * p * r / (p + r), "false_positive_rate": fp / (fp + tn)}


def main() -> None:
    d = pl.read_parquet(ROOT / "reports/experiments/anomaly/primary_scores.parquet")
    y = d["y"].to_numpy().astype(int)
    saved = {r["model"]: r for r in json.loads((ROOT / "reports/experiments/anomaly/summary.json").read_text(encoding="utf-8"))["primary"]}
    n, pos = len(y), int(y.sum())
    out = {"source": "reports/experiments/anomaly/primary_scores.parquet", "n": n, "positives": pos,
           "prevalence": pos / n, "models": {}}
    for m, col in SCORES.items():
        s = d[col].to_numpy()
        rows = {"k=positives": at_k(y, s, pos), "top_1pct": at_k(y, s, round(0.01 * n)), "top_5pct": at_k(y, s, round(0.05 * n))}
        rows["matches_saved_precision_at_k"] = abs(rows["k=positives"]["precision"] - saved[m]["precision_at_k"]) < 1e-12
        out["models"][m] = rows
    dst = ROOT / "reports/master_audit_3/anomaly_derived_metrics.json"
    dst.write_text(json.dumps(out, indent=1), encoding="utf-8")
    for m, r in out["models"].items():
        a = r["k=positives"]
        print(f"{m:30s} P=R=F1@k {a['f1']:.4f}  FPR@k {a['false_positive_rate']:.4f}  "
              f"top5% P {r['top_5pct']['precision']:.4f} R {r['top_5pct']['recall']:.4f} FPR {r['top_5pct']['false_positive_rate']:.4f}"
              f"  matches_saved={r['matches_saved_precision_at_k']}")


if __name__ == "__main__":
    main()
