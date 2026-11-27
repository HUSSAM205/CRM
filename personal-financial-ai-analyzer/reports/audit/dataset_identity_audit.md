# Dataset Identity Audit (independent re-verification)

Run 2026-11-27 (final audit). Commands: `python scripts/verify_dataset.py` (log `logs/execution/audit_verify_dataset.log`), `curl -I` on the official URL, and `sha256sum` before and after the audit.

| Property | Academic spec (HW1 p16, HW2 p3) | Measured | Status |
|---|---|---|---|
| Repository | `ziadatalabs/FreeFinancialTransactions50M` on Hugging Face | same | PASS |
| File | `transactions_50M.parquet` | same | PASS |
| URL | huggingface.co/datasets/ziadatalabs/FreeFinancialTransactions50M | `resolve/main` → HTTP 302, `x-repo-commit 98cf38f9b2f1a9994930f52a4d490cb2b5777acc` | PASS |
| Revision | not recorded in HW ("will be recorded") | commit `98cf38f9…`; file uploaded in `3a5ad0d0…` (2026-08-16) and unchanged since | PASS |
| Size | "≈1.59 GB" | 1,594,749,644 bytes (official `x-linked-size` is identical) | PASS |
| SHA-256 | to be recorded | `b18c83595d2e7a06598c00a3cbe01eb0586b2f0b10443305c6283586c27f8c17`; official LFS `x-linked-etag` is identical | PASS |
| Local path | — | `data/raw/transactions_50M.parquet` (not in git) | — |
| Row groups / rows | 50,000,000 | 50 × 1,000,000; footer = sum of row groups = rows actually read = 50,000,000 | PASS |
| Columns / types | 9 | `transaction_id, account_id, transaction_type, currency, merchant_category, transaction_timestamp, status` (string); `amount, balance_after` (double) | PASS |
| Coverage | 2024-01-01 … 2026-07-31 | 2024-01-01 00:00:03 … 2026-07-31 23:59:59; 943/943 days; 0 unparseable | PASS |
| Nulls | — | 0 in all 9 columns | PASS |
| Duplicate IDs | — | 0 (50,000,000 unique; 200 IDs carry a suffix, flagged) | PASS |
| Invalid numbers | — | 0 non-finite, negative or zero amounts; 0 with more than 2 decimals | PASS |
| Currencies / categories / types / statuses | 6 / 14 / 8 / 4 | same (distributions in `reports/data_audit/*.csv`) | PASS |
| Accounts | to be measured | 1,000,000 (20–92 transactions each) | PASS |
| **Immutability** | must not change | SHA-256 before = after (`dataset_immutability.txt`); mtime unchanged since download | PASS |

All 27 automated integrity checks: PASS (`reports/verification/dataset_integrity.json`). The official source was reachable and checked live, so the verification did not depend on earlier manifests.
