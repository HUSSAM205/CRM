# Anomaly detection (review candidates, never fraud)

## Experiment E3 (HW2 5.5, 8.4)

* **Population:** 10,000 accounts. History 2024-01..2026-04 (223,654 spending rows); scored rows in 2026-05..07: 24,069.
* **Injection:**
  * rates 0.5%, 1% and 2%; seeds 42, 43 and 44;
  * three scenario types: amount ×U(5,10), an unseen hour, and the least-used category;
  * labels and original rows are kept in `reports/experiments/anomaly/injections/`;
  * labels are never model inputs, and injected rows are test-period only (leakage test L10).
* **Methods:**
  * robust z-score (median and MAD of log amount, account-specific);
  * per-account Isolation Forest;
  * global Isolation Forest on account-relative features (the deployed artifact). Features: log amount, hour, weekday, category history share, amount relative to the account-category median. Account ID is never a feature.

| 1%, seed 42, k = 241 | ROC-AUC | Precision = recall = F1 @k | FPR @k |
|---|---|---|---|
| robust z | 0.581 | 0.037 | 0.97% |
| IF per account | 0.559 | 0.008 | 1.00% |
| IF global (deployed) | 0.587 | 0.041 | 0.97% |

* **By scenario (robust z):** amount AUC 0.80; hour 0.53; category 0.43. Hours and categories are near-uniform in this synthetic data.
* **Positive control:** ×1000 gives AUC 0.999.
* **Recomputation:** metrics were recomputed independently from the saved scores (|Δ| = 0).

## In the app

* **Label:** "Unusual transaction — review recommended." plus "This is a statistical comparison with your own history, not a fraud finding."
* **Each alert shows:** transaction ID, timestamp, category, amount, currency, the usual amount in the user's history, an explanation (or "no single rule triggered"), robust z and IF score. The method and limitations appear in the caption.
* **Shown:** only the top 5, to limit false alarms. The measured precision on the benchmark was about 1 in 24.
