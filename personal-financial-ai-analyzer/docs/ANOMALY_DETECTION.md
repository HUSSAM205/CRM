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

## Experiment E3-B on Dataset B identity-theft labels (master audit 2)

`scripts/research/anomaly_dataset_b.py`.
* **Data:** PersonaLedger sequences, each one user-month with a different user's day injected, labelled `is_fraud`. The 3,135 unlabelled sequences were excluded before any metric was computed.
* **Runs:** 5,000 sequences per run, seeds 42, 43 and 44.
* **Scoring:** unsupervised, per sequence.

| Method (mean of 3 seeds) | ROC-AUC | Avg. precision | F1@k | FPR@k | Top-1 hit rate |
|---|---|---|---|---|---|
| robust z | 0.488 | 0.031 | 0.021 | 3.4% | 2.1% |
| IF, 5 HW2 features | 0.477 | 0.032 | 0.029 | 3.4% | 3.6% |
| IF, 7 features (+ merchant novelty, card present) | 0.520 | 0.035 | 0.029 | 3.4% | 3.0% |

The base rate is about 3.4% fraud rows. **All three are at chance level.** A stranger's day of ordinary spending is not unusual relative to the victim's own history on these features. This is a negative finding: **the app cannot detect identity theft of this kind**, and nothing in the product claims it can.

## Controlled test C4 (Dataset C) and a product change (M-14)

The app's ranking was tested on 50 injected cases per type.

| Type | Before (top 5 by Isolation Forest score only) | After (top 5 by score + up to 5 rule hits) |
|---|---|---|
| Unusual amount (×8) | 92% | 100% |
| Unusual hour (03:xx) | 6% | 94% |
| Rare category (never seen) | 0% | 82% |
| Share of shown items that were injected | 19.6% | 32.3% |

Rule hits were already explained in the alert text but never shown, so they are now always surfaced, with at most 10 per account. Each alert carries one of the standard labels: *Unusual amount*, *Unusual timing*, *Rare category*, *Insufficient historical context*, or *Unusual combination*.

Dataset C was generated with these anomaly types, so this is a behaviour check, **not** independent validation. HW2 E3 metrics measure model scores and are unchanged.
