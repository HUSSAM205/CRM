"""4. AI predictions: next-month spending outlook, model comparison and quality gate, unusual-transaction
review, limitations (HW1 F6, F7, S7; HW2 5.4, 5.5; master audit 7.7-7.12). Saved models and configurations
are loaded, never retrained."""
from __future__ import annotations

import json

import polars as pl
import streamlit as st

from app.components import alerts, charts, tables
from app.utils import session
from app.utils.formatting import money
from src.models.anomaly.anomaly_scoring import model_metrics, review_candidates
from src.models.forecasting.inference import forecast_next, outlook_next, series_from_monthly
from src.utils.configuration import PROJECT_ROOT

QG = PROJECT_ROOT / "reports/experiments/forecasting_quality_gate/summary.json"


def _series(s, acc, cur) -> pl.DataFrame:
    return s.monthly.filter((pl.col("account_id") == acc) & (pl.col("currency") == cur))


def forecast_for(s, acc, cur) -> dict:
    """What the product reports as next month's estimate (used by the assistant too): the outlook (D-22)."""
    return outlook_next(_series(s, acc, cur))


def render() -> None:
    st.header("AI predictions")
    st.caption(alerts.DISCLAIMER)
    if alerts.need_data():
        return
    d = session.get_data()
    s, acc, cur = d["summaries"], st.session_state["account"], st.session_state["currency"]
    mon = _series(s, acc, cur)

    st.subheader("Next-month spending outlook")
    f = outlook_next(mon)
    months, y, _ = series_from_monthly(mon) if not mon.is_empty() else ([], [], 0)
    if not f["eligible"]:
        st.warning(f["message"])
        if len(months):
            st.plotly_chart(charts.forecast_chart(months, y, {}, None, None, cur), width="stretch")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Typical spending for {f['target_month']}", money(f["point_cents"], cur),
                  help="Median of your monthly expenses so far (deterministic). Chosen on validation data among "
                       "data-dependent baselines; no machine-learning model passed the quality gate.")
        lo, hi = f["historical_range_cents"]
        c2.metric("Your usual range (10th–90th percentile)", f"{money(lo, cur)} – {money(hi, cur)}",
                  help="Range of your own past months. Descriptive, not a calibrated prediction interval.")
        if f["benchmark_interval_cents"]:
            blo, bhi = f["benchmark_interval_cents"]
            c3.metric(f"{int(f['benchmark_interval_level'] * 100)}% interval (benchmark-calibrated)",
                      f"{money(blo, cur)} – {money(bhi, cur)}",
                      help=f"Calibrated on validation residuals of the public synthetic data; it covered "
                           f"{f['benchmark_test_coverage']:.1%} of test months there. For your own data it is indicative.")
        st.plotly_chart(charts.forecast_chart(months, y, {}, f["target_month"], f["point_cents"] / 100, cur),
                        width="stretch")
        st.info("**Machine-learning forecasting: NOT EFFECTIVE on the evaluation data.** No model (gradient boosting "
                "with standard or extended features) beat a constant zero-spending guess on validation, because the "
                "synthetic monthly spending has no repeatable pattern. The figure above is therefore a transparent "
                "historical reference, not a prediction. It cannot know about future events.")
        with st.expander("Academic experiment (HW2 E2): gradient boosting estimate"):
            g = forecast_next(mon)
            if g.get("eligible"):
                st.write(f"The frozen HW2 selection rule kept **{g['model']}**; its estimate for {g['target_month']} is "
                         f"{money(g['forecast_cents'], cur)}. The product quality gate **rejected** it "
                         f"(validation MAE above the zero baseline), so it is shown for the record only.")
            else:
                st.write(g.get("message", ""))

    if QG.exists():
        with st.expander("Model comparison and quality gate (offline evaluation on the public dataset)"):
            p = json.loads(QG.read_text())["primary"]
            rows = [{"model": m, "split": sp, "MAE": round(v["MAE"], 3), "MASE": round(v["MASE"], 4),
                     "RMSE": round(v["RMSE"], 2), "zero predictions": f"{v['zero_prediction_share']:.0%}",
                     "status": p["gate"].get(m, "product outlook" if m == p["product_outlook"] else "baseline")}
                    for sp in ("validation", "test") for m, v in sorted(p[sp].items(), key=lambda x: x[1]["MAE"])]
            st.dataframe(pl.DataFrame(rows), hide_index=True, width="stretch")
            st.caption("Gate rule (fixed before test scoring): an ML model is accepted only if it beats every "
                       "deterministic baseline, including zero, on validation MAE and MASE. "
                       f"Result: {', '.join(f'{k}: {v}' for k, v in p['gate'].items())}.")

    st.subheader("Unusual transactions")
    r = review_candidates(d["clean"], acc, cur)
    if not r["ok"]:
        st.info(r["message"])
    else:
        st.warning(f"**{r['label']}** {r['not_fraud']}")
        st.caption(f"Recent window {r['window']}: {r['scored_records']} spending records compared with "
                   f"{r['history_records']} earlier ones. Method: {r['method']}. {r['limitations']}")
        tables.show(r["candidates"], height=240)
    am = model_metrics()
    if am:
        with st.expander("How well does the unusual-transaction ranking work? (synthetic injection test)"):
            st.dataframe(pl.DataFrame(am["primary"]).select("model", "positives", "precision_at_k", "recall_at_k",
                                                            "roc_auc"), hide_index=True, width="stretch")
    with st.expander("Limitations"):
        st.markdown("- All models were evaluated on a **synthetic** public dataset; real behaviour differs.\n"
                    "- An outlook needs at least 12 active months; otherwise none is shown.\n"
                    "- Unusual transactions are statistical outliers compared with your own history, **not fraud findings**.\n"
                    "- No income is forecast: the data has no salary labels.\n"
                    "- Transaction-derived figures are not a bank balance: opening balances and other accounts are unknown.")
