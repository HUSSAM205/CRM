# Financial Calculation Audit

| Calculation | Implementation | Independent expectation | Result |
|---|---|---|---|
| Income, expenses, net, refunds, fees, transfers | `src/analytics/financial_metrics.py` (integer cents) | Hand fixture (19 rows); PyArrow full-data recomputation; pandas + `Decimal` on about 2M rows | Exact (54/54 full-scale; 0 mismatches) |
| Monthly and category spending | `monthly_summary`, `category_spending` | Hand values (`test_aggregation.py`, `test_financial_rules.py`) | Exact |
| Account balances | **Not computed.** `balance_after` is excluded (D-03) | — | N/A, by design |
| Budgets, utilization, recommendations | `src/budget/*` | Hand medians and 80%/100% thresholds (`test_budget.py`); saved edits drive alerts (`test_saved_budget_changes_drive_alerts_and_assistant`) | Exact |
| Spending comparison | `src/analytics/monthly_analysis.py` | Hand values | Exact |
| Currency conversion | Not implemented: currencies are never mixed | — | N/A, by design |
| Forecasted spending | Saved model (`inference.py`) | Fresh-process reproduction of the recorded predictions | Exact |

## Edge cases tested

* zero transactions (empty file);
* one transaction;
* negative amounts (rejected when a type is given; sign-derived types otherwise);
* refunds only (negative net);
* several currencies;
* missing categories;
* duplicate IDs;
* **very large amounts**: exact cents up to 9,999,999,999,999.99, and anything above 10¹² rejected;
* decimal precision: 0.10 + 0.20 is exact, 0.015 is rejected;
* empty months (zero-filled within the observed range);
* account switching;
* invalid timestamps.

## Defect found: A-01 (P1)

An amount of `92233720368547758.07` made `validate_transactions` raise an uncaught `InvalidOperationError` (int64-cents overflow). In the app this would have crashed an upload, which breaks HW1 P1.

* **Fix:** a new rejection reason `amount_out_of_range` for |amount| > 10¹².
* **Evidence:** the regression test fails on the old code and passes on the new code (session log).
