# Final Results and Discussion

Measured tables (HW2 Tables 9.1 and 9.2, filled in) are in `reports/final_evidence/results_tables.md`, which is generated from result files. This page interprets them.

## E1: financial correctness. PASS

Hand-calculated fixtures match exactly. Real data cross-checked against an independent `Decimal` computation: 0 mismatches over about 1.45M groups. The ledger shows the sign convention holds for 49,000,000 of 49,000,000 records.

## E2: forecasting

* Following HW2's procedure, GBR (and ETS) beat the best baseline, MA(3), on validation MAE and MASE. **GBR was selected**: validation MAE 26.55 against 42.51, MASE 0.551 against 0.845. Test MAE is 27.19 (`gbr_seasonal` 26.23).
* The result is stable across three seed resamples and when GBR is trained on **different accounts** (account-disjoint test MAE 26.80).
* **Interpretation (important).** A post-hoc diagnostic shows that a constant zero forecast is better on MAE and MASE: test 25.37 / 0.532, validation 24.70 / 0.511. Within-series autocorrelation is about −0.044, which is consistent with i.i.d. data.
  * The GBR has learned to forecast values near the median, which is 0 for these intermittent series. That is not temporal structure.
  * The HW2 baseline set has no constant-median baseline, so the rule "passes" a model with no real skill.
  * Recommendation for the final report: add a zero or median baseline, or a metric robust to intermittency, in future work. The selection was **not** changed after seeing the test data.

## E3: anomaly ranking

* Overall ROC-AUC is about 0.56–0.59 at a 1% rate. Precision@k is 0.008–0.04, against 0.01 for random ranking.
* By scenario:
  * amount ×5–10: AUC 0.80 (z-score), 0.75 (global IF), 0.64 (per-account IF);
  * hour and category: about 0.5.
* The robust z-score is equal or better on amounts. Isolation Forest's extra features add little, because hour and category carry no signal in this data.
* The positive-control dose-response (×5: 0.70, ×10: 0.84, ×50: 0.97, ×1000: 0.999) confirms the pipeline is correct.

## E4: dashboard and assistant tasks

12/12 scripted real-browser tasks completed (`reports/ux_tasks/ux_task_results.json`). Supported assistant answers equal the dashboard values (tests). Unsupported questions get the fixed reply.

## Conclusion

The deterministic core, which HW1 identifies as the part that must be correct, is verified exactly at 50M-row scale. The ML components are implemented and evaluated exactly as HW2 specifies. The honest finding is that this synthetic dataset gives them nothing to learn. That is a property of the data, demonstrated with controls, not a pipeline failure.
