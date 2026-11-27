# Financial Rules

Implemented in `src/rules/` and `src/analytics/financial_metrics.py`. Tested in `tests/unit/test_financial_rules.py`, which uses hand-calculated fixtures, and cross-checked on real data with `scripts/workers/crosscheck_partition.py`.

## Type → meaning (HW2 5.2)

| transaction_type | Meaning | Balance direction (measured) | Counts toward |
|---|---|---|---|
| debit | outflow | −amount | expenses, category spending |
| withdrawal | outflow | −amount | expenses, category spending |
| fee | fee | −amount | expenses (separate line; not category spending) |
| credit | inflow | +amount | income ("inflow"; never assumed to be salary) |
| deposit | inflow | +amount | income |
| interest | inflow | +amount | income |
| refund | refund | +amount | reduces expenses and its own category's spending |
| transfer | transfer | −amount | **neither** income nor expenses; reported separately (CF-08) |
| anything else | unresolved | — | excluded from totals; counted in `unresolved_type_records` |

**Evidence for the directions:** in transaction-ID order, 49,000,000 of 49,000,000 records satisfy Δbalance = direction × amount for completed records and Δbalance = 0 otherwise (`reports/verification/ledger_semantics_report.md`). The `amount` column holds non-negative magnitudes: 0 negative and 0 zero values across all 50M rows.

## Status (HW1 F2, HW2 5.2)

Only `completed` records enter totals. `pending`, `failed` and `reversed` are kept, excluded from totals, and counted (`excluded_status_records`, and `status_report()`). The ledger independently confirms that these statuses never move the balance.

## Formulas (all integer cents, per account × currency × month, completed only)

```
income        = Σ inflow
outflow       = Σ outflow
expenses      = outflow + fee − refund
net cash flow = income − expenses
category net  = Σ outflow(category) − Σ refund(category)
identity      : Σ category net + fee = expenses
```

## Refunds

A refund reduces spending in the same account, currency, category and calendar month as the refund itself, because the dataset does not link a refund to its purchase. Net category spending can be negative and is **not** clipped. The fixture tests this case: A1/USD/2026-02 dining = −29.99.

## Currency

Every aggregation key includes `currency` (`require_currency_key`), so a mixed-currency sum raises `MixedCurrencyError`. There is no conversion. Note that amounts have the same distribution in every currency (median about 30 everywhere, including JPY), so the currency label is synthetic.

## Verification

| Check | Result |
|---|---|
| Hand-calculated fixture: 4 monthly summaries, 7 category rows | exact match (pytest) |
| Transfers excluded; pending, failed and reversed excluded; unresolved types excluded | tests pass |
| Real data, 2 partitions, about 2.0M rows, about 1.45M groups × 4 values against independent pandas + `Decimal` | **0 mismatches** |
