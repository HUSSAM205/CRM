# Data Quality

The full audit covers all 50,000,000 rows. Details: `reports/verification/dataset_quality_report.md` and `reports/data_audit/`.

* 0 missing values, 0 duplicate IDs, 0 same-content duplicates, 0 invalid timestamps or amounts, 0 unknown codes.
* 200 IDs with an unexplained suffix (kept, flagged).
* 110 log-IQR outliers (kept).
* 854,494 negative-balance rows in 37,742 accounts (informational; the balance is unused).
* Distributions are near-uniform (hours, weekdays, categories) and identical across currencies. That limits ML signal (`docs/KNOWN_LIMITATIONS.md`).
