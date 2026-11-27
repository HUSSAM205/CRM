# Financial Rules Validation

Generated 2026-11-27 04:06 UTC. Rules: `docs/FINANCIAL_RULES.md`.

## 1. Sign convention: measured on all data
49,000,000 / 49,000,000 records reconcile `balance_after` in transaction-ID order under the documented directions
(`ledger_semantics_report.md`). Pending, failed and reversed records never change the balance.

## 2. Hand-calculated fixtures (E1, HW2 10.2)
Fixture `tests/fixtures/sample_transactions.csv` (19 rows: 2 accounts, 2 currencies, 2 months; covers income, expenses,
transfers, refunds incl. a negative category net, fees, pending, failed, reversed). Expected values in
`tests/fixtures/expected_financial_results.json` were computed by hand, with the arithmetic shown.
Latest pytest run: `27 passed in 0.28s` (`logs/testing/unit_rules_validation.log`).

## 3. Real-data independent cross-check
Validator plus `financial_metrics` compared with an independent pandas + `Decimal` recomputation
(`scripts/workers/crosscheck_partition.py`). Per group: income, expenses, net, transfers.

| Partition | Rows | Rejected | Unresolved types | Independent groups | Value mismatches | Groups missing |
|---|---|---|---|---|---|---|
| 7 | 999,683 | 0 | 0 | 725,984 | 0 | 0 |
| 33 | 1,000,786 | 0 | 0 | 726,260 | 0 | 0 |

## Verdict
Financial rules: **PASS**. Totals are exact (integer cents), currencies are never combined, transfers are neutral,
refunds reduce category spending, and non-completed and unresolved records are excluded and counted.
