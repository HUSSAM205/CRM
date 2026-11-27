"""Post-hoc evaluation of saved results (diagnostics, figures). Never re-selects models.

Forecasting: error analysis on the primary TEST predictions (src/evaluation/error_analysis.py).
Writes reports/evaluation/forecasting_error_analysis.json and figures in reports/figures/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluation.error_analysis import analyse  # noqa: E402
from src.experiments import forecasting_experiment as fe  # noqa: E402


def forecasting() -> dict:
    keys, Y = fe.load_panel(ROOT / "data/processed/splits/panel_primary.parquet")
    tp = pl.read_parquet(ROOT / "reports/experiments/forecasting/test_predictions.parquet")
    models = [c for c in tp.columns if c not in ("account_id", "currency", "month", "actual")]
    preds = {}
    for m in models:
        wide = tp.pivot(on="month", index=["account_id", "currency"], values=m)
        wide = keys.select("account_id", "currency").join(wide, on=["account_id", "currency"], how="left")
        preds[m] = wide.select(sorted(c for c in wide.columns if c[:2] == "20")).to_numpy()
    # sanity: the actuals stored with the predictions equal the panel (alignment check)
    act = keys.select("account_id", "currency").join(
        tp.pivot(on="month", index=["account_id", "currency"], values="actual"), on=["account_id", "currency"])
    assert np.allclose(act.select(sorted(c for c in act.columns if c[:2] == "20")).to_numpy(), Y[:, fe.TEST_COLS])
    res = analyse(Y, preds, fe.TEST_COLS, fe.N_TRAIN, fe.N_TRAIN + fe.N_VAL)
    res["note"] = "Diagnostic only; reference predictors are NOT HW2 baselines and were NOT used for selection."
    return res


def main() -> None:
    out = ROOT / "reports/evaluation"
    out.mkdir(parents=True, exist_ok=True)
    f = forecasting()
    (out / "forecasting_error_analysis.json").write_text(json.dumps(f, indent=2), encoding="utf-8")
    rows = [{"kind": "model", "name": k, **{m: round(v[m], 3) for m in ("MAE", "RMSE", "MASE")}} for k, v in f["models"].items()]
    rows += [{"kind": "reference (diagnostic)", "name": k, **{m: round(v[m], 3) for m in ("MAE", "RMSE", "MASE")}}
             for k, v in f["reference"].items()]
    pl.DataFrame(rows).sort("MAE").write_csv(out / "forecasting_test_with_reference_predictors.csv")
    print(pl.DataFrame(rows).sort("MAE"))
    print("actual zero share (test):", round(f["actual_zero_share"], 3))
    print(json.dumps(f["prediction_spread"], indent=1))
    print(json.dumps(f["error_by_month_type"], indent=1))


if __name__ == "__main__":
    main()
