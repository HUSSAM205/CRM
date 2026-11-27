# Phase 5: Anomaly Audit

Status: **COMPLETE**. Details: `docs/ANOMALY_DETECTION.md`, `ANOMALY_EXPERIMENTS.md`.

| Experiment | Data | Result |
|---|---|---|
| E3 (HW2) | A, injected 0.5/1/2% × 3 seeds | AUC 0.56–0.62; F1@k ≤ 0.041; amount anomalies AUC 0.80 |
| E3-B | B identity theft, 3 seeds × 5,000 sequences | **chance level** (AUC 0.48–0.52) for z-score, IF with 5 features and IF with 7 features (feature-engineering variant) |
| C4 | C, 50 per type | ranking by IF only: amount 92%, hour 6%, category 0% → after M-14 (rule hits surfaced): 100 / 94 / 82% |

**User-facing language:** "Unusual transaction — review recommended." plus "not a fraud finding", with per-alert labels (Unusual amount, Unusual timing, Rare category, Insufficient historical context, Unusual combination) and the evidence columns.

**Status:** PASS **for the evaluated scope only**: large-amount outliers and clear rule breaks. Identity-theft-like behaviour is not detectable, and no fraud capability is claimed.
