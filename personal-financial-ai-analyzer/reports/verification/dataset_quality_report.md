# Dataset Quality Report

Generated 2026-11-27 03:17 UTC. Scope: **all 50,000,000 rows, 1,000,000 accounts (no sampling)**.
Scripts: `scripts/run_audit.py` (+ workers). Raw tables: `reports/data_audit/`.

## Summary of findings
| Check (HW1 4.4 / HW2 4.4) | Result | Status |
|---|---|---|
| Missing values (null or blank), all 9 columns | 0 | PASS |
| Duplicate transaction_id | 0 | PASS |
| Fully duplicated rows | 0 (implied by unique IDs) | PASS |
| Same content, different ID | 0 | PASS |
| Non-standard IDs (suffix `-zdl26nr51f60aaa959f`) | 200 | FLAGGED, kept (D-05) |
| Invalid / unparseable timestamps | 0 | PASS |
| Calendar days present | 943 (2024-01-01 … 2026-07-31; full range = 943) | PASS |
| Non-finite / negative / zero amounts | 0 / 0 / 0 | PASS |
| Amounts with more than 2 decimals | 0 | PASS |
| Unknown currency / type / status / category | 0 / 0 / 0 / 0 (see integrity report domains) | PASS |
| Sign consistency (ledger) | 49,000,000/49,000,000 records reconcile | PASS |
| Amount outliers, log-IQR×3 rule | 48 high (> 5397.08), 62 low (< 0.17) | Investigated, **kept** |
| Negative balance rows / accounts | 854,494 rows / 37,742 accounts | Informational (balance unused) |
| Transactions per account | min 20, max 92 | — |

## Account statistics (quantiles across 1,000,000 accounts)
| metric | q0.0 | q0.01 | q0.05 | q0.25 | q0.5 | q0.75 | q0.95 | q0.99 | q1.0 | mean |
|---|---|---|---|---|---|---|---|---|---|---|
| n_tx | 20.0 | 34.0 | 39.0 | 45.0 | 50.0 | 55.0 | 62.0 | 67.0 | 92.0 | 50.0 |
| n_completed | 16.0 | 31.0 | 35.0 | 41.0 | 46.0 | 50.0 | 57.0 | 62.0 | 83.0 | 45.999107 |
| active_months_any | 12.0 | 19.0 | 21.0 | 23.0 | 25.0 | 26.0 | 28.0 | 29.0 | 31.0 | 24.814455 |
| active_spending_months | 5.0 | 11.0 | 13.0 | 15.0 | 17.0 | 19.0 | 22.0 | 23.0 | 29.0 | 17.082325 |
| n_currencies | 2.0 | 4.0 | 5.0 | 6.0 | 6.0 | 6.0 | 6.0 | 6.0 | 6.0 | 5.799019 |
| n_categories | 7.0 | 12.0 | 12.0 | 13.0 | 14.0 | 14.0 | 14.0 | 14.0 | 14.0 | 13.606241 |
| max_gap_days | 32.0 | 48.0 | 55.0 | 67.0 | 79.0 | 95.0 | 126.0 | 156.0 | 347.0 | 83.416164 |
| negative_balance_rows | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 33.0 | 70.0 | 0.854494 |

## Monthly coverage
| month | rows | completed_rows | active_accounts |
|---|---|---|---|
| 2024-01 | 1641906 | 1510729 | 806416 |
| 2024-02 | 1537211 | 1414650 | 784958 |
| 2024-03 | 1643662 | 1512287 | 806562 |
| 2024-04 | 1592020 | 1464967 | 796420 |
| 2024-05 | 1643460 | 1511918 | 806619 |
| 2024-06 | 1589162 | 1462156 | 795765 |
| 2024-07 | 1644606 | 1512990 | 807005 |
| 2024-08 | 1642559 | 1511084 | 806821 |
| 2024-09 | 1590967 | 1463713 | 796401 |
| 2024-10 | 1642841 | 1511768 | 806123 |
| 2024-11 | 1591274 | 1463946 | 796384 |
| 2024-12 | 1642115 | 1510840 | 806286 |
| 2025-01 | 1645574 | 1514041 | 807014 |
| 2025-02 | 1484356 | 1365365 | 773221 |
| 2025-03 | 1642504 | 1510848 | 806422 |
| 2025-04 | 1591603 | 1464317 | 796792 |
| 2025-05 | 1643248 | 1511570 | 806439 |
| 2025-06 | 1591363 | 1464710 | 797066 |
| 2025-07 | 1646574 | 1515485 | 807320 |
| 2025-08 | 1644587 | 1513007 | 806290 |
| 2025-09 | 1589830 | 1462463 | 796339 |
| 2025-10 | 1642364 | 1510609 | 806070 |
| 2025-11 | 1589235 | 1461783 | 795691 |
| 2025-12 | 1645030 | 1513172 | 807554 |
| 2026-01 | 1642980 | 1511157 | 806309 |
| 2026-02 | 1484745 | 1365586 | 773620 |
| 2026-03 | 1645447 | 1513746 | 806734 |
| 2026-04 | 1590870 | 1463218 | 796283 |
| 2026-05 | 1643287 | 1511713 | 806795 |
| 2026-06 | 1590224 | 1462701 | 796108 |
| 2026-07 | 1644396 | 1512568 | 806628 |

## Distributions
### Status
| status | rows | share |
|---|---|---|
| completed | 45999107 | 0.919982 |
| failed | 1250047 | 0.025001 |
| pending | 2250253 | 0.045005 |
| reversed | 500593 | 0.010012 |
### Transaction type
| transaction_type | rows | share |
|---|---|---|
| credit | 9998728 | 0.199975 |
| debit | 19999177 | 0.399984 |
| deposit | 2501085 | 0.050022 |
| fee | 3000311 | 0.060006 |
| interest | 1500674 | 0.030013 |
| refund | 2001601 | 0.040032 |
| transfer | 6999417 | 0.139988 |
| withdrawal | 3999007 | 0.07998 |
### Currency
| currency | rows | share |
|---|---|---|
| AUD | 2499058 | 0.049981 |
| CAD | 3499177 | 0.069984 |
| EUR | 9001468 | 0.180029 |
| GBP | 5000059 | 0.100001 |
| JPY | 2499646 | 0.049993 |
| USD | 27500592 | 0.550012 |
### Merchant category
| merchant_category | rows | share |
|---|---|---|
| cash | 3568889 | 0.071378 |
| dining | 3573003 | 0.07146 |
| education | 3569242 | 0.071385 |
| entertainment | 3577264 | 0.071545 |
| groceries | 3573561 | 0.071471 |
| healthcare | 3572288 | 0.071446 |
| insurance | 3569356 | 0.071387 |
| other | 3572682 | 0.071454 |
| retail | 3571506 | 0.07143 |
| subscription | 3571534 | 0.071431 |
| transfer | 3571454 | 0.071429 |
| transport | 3570482 | 0.07141 |
| travel | 3568268 | 0.071365 |
| utilities | 3570471 | 0.071409 |
### Amount by currency
| currency | rows | q0.0 | q0.01 | q0.05 | q0.25 | q0.5 | q0.75 | q0.95 | q0.99 | q0.999 | q1.0 | mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AUD | 2499058 | 0.14 | 2.32 | 4.92 | 14.28 | 30.02 | 63.04 | 183.0 | 386.82 | 903.4 | 6482.24 | 54.92844404971793 |
| CAD | 3499177 | 0.11 | 2.31 | 4.9 | 14.27 | 29.96 | 62.9 | 182.68 | 387.36 | 899.38 | 7819.13 | 54.86709243059151 |
| EUR | 9001468 | 0.09 | 2.32 | 4.91 | 14.28 | 29.98 | 62.91 | 182.83 | 387.33 | 895.38 | 7465.19 | 54.86863169985162 |
| GBP | 5000059 | 0.06 | 2.31 | 4.9 | 14.26 | 29.96 | 62.93 | 182.97 | 388.09 | 898.82 | 6464.4 | 54.91400375875564 |
| JPY | 2499646 | 0.08 | 2.32 | 4.91 | 14.28 | 29.99 | 63.01 | 183.06 | 387.01 | 890.17 | 6672.18 | 54.87919944264107 |
| USD | 27500592 | 0.06 | 2.32 | 4.91 | 14.27 | 29.96 | 62.91 | 183.05 | 387.38 | 895.35 | 9213.81 | 54.87485628963913 |
### Hour of day
| hour | rows |
|---|---|
| 0 | 2083914 |
| 1 | 2085739 |
| 2 | 2082868 |
| 3 | 2082128 |
| 4 | 2082824 |
| 5 | 2083943 |
| 6 | 2083017 |
| 7 | 2084378 |
| 8 | 2085547 |
| 9 | 2083314 |
| 10 | 2083964 |
| 11 | 2083698 |
| 12 | 2082240 |
| 13 | 2083394 |
| 14 | 2084489 |
| 15 | 2081984 |
| 16 | 2081234 |
| 17 | 2082374 |
| 18 | 2082988 |
| 19 | 2082574 |
| 20 | 2084997 |
| 21 | 2084105 |
| 22 | 2084160 |
| 23 | 2080127 |
### ISO weekday (1 = Monday)
| iso_weekday | rows |
|---|---|
| 1 | 7156754 |
| 2 | 7158482 |
| 3 | 7160018 |
| 4 | 7160469 |
| 5 | 7157773 |
| 6 | 7101931 |
| 7 | 7104573 |
### Accounts by number of currencies used
| n_currencies | count |
|---|---|
| 2 | 2 |
| 3 | 282 |
| 4 | 12217 |
| 5 | 175693 |
| 6 | 811806 |

## Interpretation (limits of the synthetic data)
* Hours, weekdays, categories and amount distributions are near-uniform or identical across groups. The data has
  little behavioural structure, so ML results must be read as a methodology demonstration (see `docs/limitations.md`).
* Amount distributions are identical in every currency (median about 30 for USD and JPY alike). Currency is a label,
  not a real currency scale.
* Outliers are rare and consistent with the documented log-normal amounts. They are not removed.
