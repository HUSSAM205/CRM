# Anomaly Detection Audit

## Protocol

* Population: 10,000 accounts. History (fit) is 2024-01..2026-04: 223,654 rows. Scored test window is 2026-05..07: 24,069 rows. 0 accounts lack history.
* Injection (HW2 8.4): rates 0.5%, 1% and 2%; seeds 42, 43 and 44. There are three scenario types: amount ×U(5,10), an unseen hour, and the least-used category. Injected rows are test-period only and never in history (L10 test, which passes when the data is present).
* Models: robust z on log amount (per-account and per-category history statistics); per-account Isolation Forest (HW2 5.5); global Isolation Forest (the deployed artifact, D-07).
* Labeling in the UI: "Anomaly review candidate (not confirmed fraud)" (UX task 9). The words "fraud detected" never appear.

## Results at the primary setting (1%, seed 42; k = number of positives = 241). Independent recomputation from saved scores.

| Model | ROC-AUC | Avg. precision | Precision = recall = F1 @k | TP / FP @k | FPR @k |
|---|---|---|---|---|---|
| robust z | 0.581 | 0.0168 | 0.037 | 9 / 232 | 0.97% |
| IF per account | 0.559 | 0.0112 | 0.008 | 2 / 239 | 1.00% |
| IF global (deployed) | 0.587 | 0.0154 | 0.041 | 10 / 231 | 0.97% |

* The random-ranking reference for precision@k is 0.01.
* Robustness: mean over 3 seeds, ROC-AUC 0.56–0.62 across rates (`robustness_by_rate.csv`).
* By scenario (robust z): amount AUC 0.80, hour 0.53, category 0.43.
* The positive control (×1000 amount) reaches AUC 0.999, so the pipeline is functional.
* Reproduction: 27 rows, max |Δ| = 0.0.

## Conclusion

The detector ranks large-amount deviations above chance. It is **not** a reliable fraud detector, and the documentation never claims it is: an F1 of 0.04 at a 1% false-positive rate means about 23 of every 24 flagged rows are normal. The hour and category scenarios are undetectable because this synthetic data is near-uniform in both (O-03). The per-account IF, as HW2 specifies it, performs worst (about 22 history rows per account).
