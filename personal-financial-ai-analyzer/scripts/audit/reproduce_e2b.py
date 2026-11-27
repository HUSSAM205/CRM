"""Master audit 3: independent, READ-ONLY reproduction of the E2-B headline numbers.

Rebuilds the Dataset B rows from the source parquet (same row builder as the experiment), loads the SAVED
model artifact (no retraining) and its saved interval, and recomputes on the test months: model MAE, the
historical-median baseline MAE, the relative gain and the 80% interval coverage. Nothing in artifacts/ or
reports/experiments/ is written. Output: reports/master_audit_3/e2b_reproduction.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/research"))
import forecast_dataset_b as E


def main() -> int:
    summ = json.loads((E.OUT / "summary.json").read_text(encoding="utf-8"))
    d = ROOT / summ["artifact"]
    model, meta = joblib.load(d / "model.joblib"), json.loads((d / "metadata.json").read_text(encoding="utf-8"))
    rows = E.build_rows()
    te = rows.filter(pl.col("month").is_between(pl.lit(E.TEST[0]), pl.lit(E.TEST[1])))
    p, y = E.predict(model, te), te["y"].to_numpy()
    iv = meta["interval"]
    b = np.digitize(p, np.array(iv["edges"]))
    cov = float(np.mean([iv["ratio_quantiles"][str(k)][0] * pk <= yk <= iv["ratio_quantiles"][str(k)][1] * pk
                         for k, pk, yk in zip(b, p, y)]))
    mae_m = float(np.abs(p - y).mean())
    mae_b = float(np.abs(te["historical_median"].to_numpy() - y).mean())
    saved = summ["test"]
    out = {"test_rows": te.height, "users": te["user"].n_unique(),
           "reproduced": {"gbr_scale_free_MAE": mae_m, "historical_median_MAE": mae_b,
                          "relative_gain_vs_best_baseline": (mae_b - mae_m) / mae_b, "interval_80_test_coverage": cov},
           "saved": {"gbr_scale_free_MAE": saved["gbr_scale_free"]["MAE"],
                     "historical_median_MAE": saved["historical_median"]["MAE"],
                     "interval_80_test_coverage": summ["interval"]["test_coverage"]}}
    out["match"] = (abs(mae_m - saved["gbr_scale_free"]["MAE"]) < 1e-6 and abs(mae_b - saved["historical_median"]["MAE"]) < 1e-6
                    and abs(cov - summ["interval"]["test_coverage"]) < 1e-9)
    dst = ROOT / "reports/master_audit_3/e2b_reproduction.json"
    dst.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0 if out["match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
