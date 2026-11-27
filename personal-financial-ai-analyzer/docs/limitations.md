# Limitations

Each limitation is backed by evidence in the files referenced.

## Data (synthetic: HW1 R3)

1. **No temporal signal in monthly spending.** Within-series autocorrelation is −0.044 at lags 1, 2, 3 and 12, matching i.i.d. noise (`reports/evaluation/forecasting_error_analysis.json`).
2. **Near-uniform behaviour.** Hours (max/min ratio 1.0027), weekdays and the 14 categories are almost uniform (`reports/data_audit/*`). "Unusual hour" and "rare category" therefore have little meaning, and their injected anomalies are detected at about chance (AUC ≈ 0.5).
3. **Currency is only a label.** Amount distributions are identical in all six currencies (median about 30, including JPY).
4. **Timestamps do not follow the ledger order.** In 0 of 1,000,000 accounts does time order equal the `balance_after` sequence (`ledger_semantics_report.md`). Calendar logic assumes the timestamps are true (D-04).
5. **`balance_after` is unusable.** One balance per account mixes currencies. It is excluded everywhere (D-03).
6. **Effectively USD-only forecasting.** 106,930 of 106,945 eligible series are USD (D-14).
7. **No labels** for salary, fraud, merchant descriptions or budgets. This rules out an income forecast (CF-01), a category classifier (CF-02) and real fraud evaluation.
8. **200 IDs carry an unexplained suffix.** They are kept and their meaning is unknown (D-05).

## Methods

9. **Forecasting.** GBR passes HW2's selection rule, but a **zero forecast** has lower MAE and MASE on both validation and test, because 62% of test months are zero and MAE rewards the median. GBR is better only on RMSE against zero. The reported "improvement over baselines" must not be read as predictive skill.
10. **Anomaly ranking.** ×5–10 amounts are detected with AUC of about 0.63–0.80. The positive control (×1000: AUC 0.999) shows the pipeline itself works. The weak results reflect heavy-tailed amounts (log σ ≈ 1.1) and a lack of behavioural regularity.
11. **Per-account Isolation Forest** has only about 22 history records per account and performs worst. It also cannot score accounts it has not seen, which is why a global forest is the deployed artifact (D-07).
12. **Transfers** are assumed internal (CF-08), because the dataset has no counterparty field.
13. **Assistant** coverage is limited to five intents, recognized by English month names and keywords.

## Engineering

14. **Windows install not executed.** The pinned stack resolves for Windows/CPython 3.12 with wheels only, but no install was run on the user's laptop.
15. **Timings were measured on the cloud container,** not the laptop. The memory limits are host-independent.
16. **The UX validation is scripted** (Playwright). It is not a study with human participants.
