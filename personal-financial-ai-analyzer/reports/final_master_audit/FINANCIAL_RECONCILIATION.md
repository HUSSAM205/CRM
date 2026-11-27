# Financial Reconciliation

## 1. Full-dataset reconciliation (independent path vs production tables)

**Command:**

```bash
python scripts/audit/reconcile_granular.py
```

It was run under `run_guarded` and finished in 53.9 s with a peak RSS of 0.90 GB (`logs/execution/master_reconcile_granular.log`). The independent path is PyArrow only, with no project code, reading the raw file row group by row group. Output: `financial_reconciliation.json`.

| Level | Keys | Measures | Result |
|---|---|---|---|
| Currency × month | 186 (6 currencies × 31 months) | income, outflow, fee, refund, transfer, expenses, net cash flow, completed records, excluded-status records | exact |
| Currency × month × category | 2,604 | gross spending (debit + withdrawal), refunds, net spending | exact |
| Global | — | total records 50,000,000 = 50,000,000; distinct accounts 1,000,000 = 1,000,000 | exact |
| **Total** | | **9,488 checks** | **0 mismatches: PASS** |

Earlier currency-level reconciliation, also exact: 54/54 (`reports/audit/reconciliation.json`).

Rules verified by these equalities:
* only `completed` records count;
* transfers are neutral (excluded from income and expenses, reported separately);
* refunds reduce their own category and month;
* fees count as expenses but sit outside category spending;
* currencies are never mixed;
* integer cents, with `round(amount × 100)`. Amounts have at most 2 decimals, so this rounding is exact.

## 2. Curated reference cases (hand calculations)

| Test | Covers | Result |
|---|---|---|
| `tests/unit/test_financial_rules.py` (8 tests) | monthly spending, income, net, category totals, refunds, transfers, fees, `pending`/`failed`/`reversed` excluded (parametrized), category + fee = expenses | 100% exact |
| `tests/regression/test_financial_correctness.py` | known-answer fixture `expected_financial_results.json`; assistant equals totals | exact |
| `tests/unit/test_validation.py` (11 tests) | duplicates, missing fields, invalid amounts, out-of-range amounts (A-01), 2-decimal precision (0.10 + 0.20 exact; 0.015 rejected), large exact amounts up to 999,999,999,999.99 | exact or controlled rejection |
| `tests/unit/test_aggregation.py` | multiple accounts, multiple currencies, empty months | exact |
| Ingestion tests | empty file, header only, one row | controlled |

**Rounding policy:** no rounding of inputs. Amounts with more than 2 decimals are rejected (`amount_precision`). Display rounds cents to 2 decimals.

**Overflow:**
* Per row: |amount| > 10¹² is rejected (`amount_out_of_range`, A-01).
* Per file: **defect M-02, found and fixed in this phase.** Polars int64 sums wrap around silently. A file of 100,000 rows at the per-row bound produced total expenses of −8,446,744,073,709,651,616 cents (reproduced). Files whose absolute amounts sum to 2⁶² cents or more are now refused with a controlled error (`check_total_range`).
* Regression tests: `test_file_whose_totals_would_overflow_is_refused_not_wrapped` (fails before the fix, passes after) and `test_large_but_safe_file_totals_stay_exact`.
* The 50M dataset is far below the bound: its largest amount is 9,213.81.
