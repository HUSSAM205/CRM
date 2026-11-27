# Anomaly Experiments

Method, product behaviour and limitations: [`docs/ANOMALY_DETECTION.md`](../../docs/ANOMALY_DETECTION.md). Results:
* `reports/experiments/anomaly/` (`summary.json`, `metrics_all_runs.csv`, `robustness_by_rate.csv`, `injections/` with original and modified rows);
* independent recomputation in `reports/audit/training_audit.json`.

| Rate (3 seeds, mean) | Model | ROC-AUC | Precision@k | Precision@100 |
|---|---|---|---|---|
| 0.5% | IF global | 0.610 | 0.039 | 0.037 |
| 0.5% | IF per account | 0.568 | 0.008 | 0.007 |
| 0.5% | robust z | 0.588 | 0.039 | 0.033 |
| 1% | IF global | 0.593 | 0.051 | 0.040 |
| 1% | IF per account | 0.560 | 0.012 | 0.013 |
| 1% | robust z | 0.580 | 0.050 | 0.050 |
| 2% | IF global | 0.624 | 0.086 | 0.087 |
| 2% | IF per account | 0.587 | 0.031 | 0.020 |
| 2% | robust z | 0.605 | 0.070 | 0.107 |

**Primary run** (1%, seed 42, k = 241 positives among 24,069 rows), recomputed from saved scores:

| Model | TP / FP | Precision = recall = F1 | False-positive rate |
|---|---|---|---|
| robust z | 9 / 232 | 0.037 | 0.97% |
| IF per account | 2 / 239 | 0.008 | 1.00% |
| IF global | 10 / 231 | 0.041 | 0.97% |

**Detection rate by type** (robust z, recall@k): amount 10.5% (AUC 0.80); hour 1.3% (AUC 0.53); category 0% (AUC 0.43). Positive control: ×1000 amount gives AUC 0.999.

**Ground-truth isolation:** labels are stored apart from the scored features and never used for fitting; injected rows are test-period only (L10).

**Status:** operational but weak (PARTIAL). It is presented only as "Unusual transaction — review recommended.", top 5, with evidence. **Never fraud.**
