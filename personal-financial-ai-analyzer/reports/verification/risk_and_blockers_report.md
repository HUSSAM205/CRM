# Risks and Blockers

Updated 2026-11-27. HW1 risks R1–R8 come from Table 2.4 (p12). The "Measured now" column replaces the planning estimates with evidence.

| ID | Risk (HW1) | Measured now | Mitigation in place | Residual |
|---|---|---|---|---|
| R1 | Insufficient account history for forecasting | 106,945 account-currency series have ≥ 12 active training months; 4.9M of 5.15M series do not | 12-month eligibility rule; an "insufficient data" notice otherwise | Low. The forecastable set is effectively USD-only (D-14) |
| R2 | No merchant descriptions | Confirmed: there is no text column | No classifier; keyword rules plus "Uncategorized" for uploads | Accepted (CF-02) |
| R3 | Synthetic data differs from real data | Confirmed: uniform hours and categories; identical amount distributions across currencies; timestamps independent of the ledger | Results framed as a methodology demonstration | **Medium.** It limits the ML signal; reported honestly |
| R4 | RAM pressure | Measured: an unpartitioned aggregation needs more than 4 GB; a single-process loop grew to 12.1 GB | Partitioned child processes, guard, checkpoints (D-11) | Low (≤ 1.1 GB per worker) |
| R5 | Leakage from balance, identity or the future | `balance_after` mixes currencies and follows ID order | Excluded; train-only eligibility; L1–L12 controls | Low; tests pending |
| R6 | Currency or type errors | Sign convention measured on 49M records; currency key enforced | Rules plus tests plus cross-check | Low |
| R7 | Private data exposure | No uploads yet | Local-only app, no raw values in logs, deletion (planned and tested) | Pending app |
| R8 | Solo-developer time | — | Gated plan; core first | — |
| N1 | Memory retained by Polars inside one process (new) | 3.7 → 12.1 GB | Child process per partition | Resolved |
| N2 | 200 non-standard IDs (new) | Unique; numeric parts complete the range | Kept and flagged | Meaning unknown |

## Blockers

**None.** No item needs credentials, payment or a decision from the user. External authorization was needed once, for network access to Hugging Face; it was approved, and the dataset is downloaded.
