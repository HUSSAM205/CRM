# Dataset Identity Audit

**Gate B.** Status and evidence summary: see `FINAL_VALIDATION_REPORT.md`.

Detailed audit (methods, tables, evidence paths): [`reports/audit/dataset_identity_audit.md`](../audit/dataset_identity_audit.md).

Summary: **PASS**. `ziadatalabs/FreeFinancialTransactions50M`, commit `98cf38f9b2f1a9994930f52a4d490cb2b5777acc`, `transactions_50M.parquet`, 1,594,749,644 bytes, SHA-256 `b18c83595d2e7a06598c00a3cbe01eb0586b2f0b10443305c6283586c27f8c17` (identical to the official LFS etag). It has 50,000,000 rows (50 row groups × 1,000,000), 9 columns, 1,000,000 accounts and covers 2024-01-01..2026-07-31. Rows per split period: train 38,758,051; validation 6,364,042; test 4,877,907. The file was unchanged during the audit (`reports/audit/dataset_immutability.txt`).
