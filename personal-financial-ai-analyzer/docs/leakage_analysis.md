# Leakage Analysis

Sources: HW1 4.6 (p18), HW2 4.6 (p5), HW1 risk R5 (p12).

| # | Leakage risk | Where it could enter | Control | Verification |
|---|---|---|---|---|
| L1 | `balance_after` encodes outcomes (and mixes currencies) | Any feature set | Never selected as a feature (D-03) | Planned: `tests/regression/test_data_leakage.py` asserts it is absent from every saved feature schema |
| L2 | Future months used in features | Lags, rolling means, seasonal lag | Features for target month *t* use months ≤ *t−1* only. Rolling mean over *t−3..t−1*; seasonal lag *t−12* | Planned: a test perturbs months ≥ *t* and asserts the features for *t* do not change |
| L3 | Series selection uses the future | Eligibility rule | Eligibility counts training-period months only (D-08) | `methodology_feasibility.json`: done on 2024-01..2025-12 only |
| L4 | Model selection on test | Hyperparameters, model choice | Selection on validation (2026-01..04); test (2026-05..07) scored once (D-16) | Planned: experiment log records the selection before the test is scored |
| L5 | Scalers or encoders fitted on all data | Preprocessing | Fitted on training rows only (HW2 4.5(7)) | Planned test |
| L6 | Duplicates straddling the split | Dedup | Dedup by `transaction_id` before splitting. Measured: 0 duplicate IDs and 0 same-content rows | Audit |
| L7 | Account identity as a shortcut | `account_id` | Used only for grouping and splitting, never as a feature (HW1 Table 4.2) | Planned schema test |
| L8 | Global future category statistics | Anomaly ratio feature | The account-category median comes from the account's history **before** the scored transaction's period (training months for the test period) | Planned test |
| L9 | Future transaction counts | Features | Not used | Schema test |
| L10 | Synthetic anomaly labels in training | Anomaly models | Injection only in test-period records; models fitted on pre-test history; labels kept in a separate table | Planned test: training frames contain no injected IDs |
| L11 | Cross-account generalization | Primary split shares accounts across periods | A separate account-disjoint experiment (CF-05) with a seeded account split | Planned |
| L12 | Uploaded user data in training | App | The app never writes to `data/`; training scripts read only `data/raw` and derived files | Planned integration test |
