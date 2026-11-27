"""4. AI predictions: next-month forecast, forecast history, model comparison, anomaly review
candidates, limitations (HW1 F6, F7, S7; HW2 5.4, 5.5). Saved models are loaded, never retrained."""
from __future__ import annotations

import json

import polars as pl
import streamlit as st

from app.components import alerts, charts, tables
from app.utils import session
from app.utils.formatting import money
from src.models.anomaly.anomaly_scoring import model_metrics, review_candidates
from src.models.forecasting.inference import forecast_next, selection, series_from_monthly
from src.utils.configuration import PROJECT_ROOT


def forecast_for(s, acc, cur) -> dict:
    return forecast_next(s.monthly.filter((pl.col("account_id") == acc) & (pl.col("currency") == cur)))


def render() -> None:
    st.header("AI predictions")
    st.caption(alerts.DISCLAIMER)
    if alerts.need_data():
        return
    d = session.get_data()
    s, acc, cur = d["summaries"], st.session_state["account"], st.session_state["currency"]
    mon = s.monthly.filter((pl.col("account_id") == acc) & (pl.col("currency") == cur))

    st.subheader("Next-month spending forecast")
    f = forecast_next(mon)
    months, y, _ = series_from_monthly(mon)
    if not f["eligible"]:
        st.warning(f["message"])
        st.plotly_chart(charts.forecast_chart(months, y, {}, None, None, cur), width="stretch")
    else:
        st.metric(f"Expected spending in {f['target_month']}", money(f["forecast_cents"], cur),
                  help=f"Model: {f['model']} (chosen on validation data). Based on {f['active_months']} active months.")
        backtest = {}
        for k in range(1, 4):  # the same saved model, applied to history ending k months earlier
            past = mon.filter(pl.col("month") <= months[-1 - k])
            r = forecast_next(past, f["model"])
            if r["eligible"]:
                backtest[r["target_month"]] = r["forecast_cents"] / 100
        st.plotly_chart(charts.forecast_chart(months, y, backtest, f["target_month"], f["forecast_cents"] / 100, cur),
                        width="stretch")
        st.caption("A forecast is an estimate from past spending only; it cannot know about future events. "
                   "In the synthetic training data, monthly spending showed no repeatable month-to-month pattern "
                   "and most months had no spending, so the model tends to forecast low or zero values. "
                   "Treat it as a rough reference, not a prediction you can rely on.")

    summ = PROJECT_ROOT / "reports/experiments/forecasting/summary.json"
    if summ.exists():
        with st.expander("Model comparison (offline evaluation on the public dataset)"):
            p = json.loads(summ.read_text())["primary"]
            rows = [{"model": m, "split": sp, **{k: round(v[k], 3) for k in ("MAE", "RMSE", "MASE")}}
                    for sp in ("validation", "test") for m, v in p[sp].items()]
            st.dataframe(pl.DataFrame(rows), hide_index=True, width="stretch")
            st.caption(f"Selected by the HW2 rule on validation data: **{selection()['selected_model']}**. "
                       f"Kept advanced models: {', '.join(p['kept_advanced_models']) or 'none'}.")

    st.subheader("Anomaly review candidates")
    r = review_candidates(d["clean"], acc, cur)
    if not r["ok"]:
        st.info(r["message"])
    else:
        st.caption(f"{r['label']}. Recent window {r['window']}: {r['scored_records']} spending records compared "
                   f"with {r['history_records']} earlier ones. Ranked by {r['ranked_by']}.")
        tables.show(r["candidates"], height=320)
    am = model_metrics()
    if am:
        with st.expander("How well does anomaly ranking work? (synthetic injection test)"):
            st.dataframe(pl.DataFrame(am["primary"]).select("model", "positives", "precision_at_k", "recall_at_k",
                                                            "roc_auc"), hide_index=True, width="stretch")
    with st.expander("Limitations"):
        st.markdown("- Models were trained and evaluated on a **synthetic** public dataset; real behaviour differs.\n"
                    "- Forecasts need at least 12 active months; otherwise none is shown.\n"
                    "- Anomalies are statistical outliers compared with your own history, **not fraud findings**.\n"
                    "- No income is forecast: the data has no salary labels (see project documentation).\n"
                    "- In evaluation, a simple 'zero spending' guess was about as accurate as the model on MAE, "
                    "because the training series had no learnable pattern (see reports/evaluation).")
