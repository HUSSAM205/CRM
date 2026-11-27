# Final Academic Traceability (master audit 3)

**Sources:**
* HW1 = `ST_HW1_Hussam_Aburahmah_2357138_2.pdf`;
* HW2 = `ST_HW2_Hussam_Aburahmah_2357138_1.pdf`.

Both were read only and are unchanged.

**Statuses:**
* **PASS**: implemented and verified, with evidence re-run in this audit;
* **PARTIAL**: partly met, with what remains;
* **NOT APPLICABLE**: excluded by the HWs' own conditions;
* **NOT TESTED**: no evidence.

The detailed implementation matrix is in `docs/requirements_traceability.md`.

## HW1 functional requirements (1.2.1)

| ID | Requirement | Evidence | Status |
|---|---|---|---|
| F1 | Read the CSV, map columns, reject problem files | ingestion and validation tests; browser 1–4, 14, 26–27 (new: add/replace workflow) | PASS |
| F2 | Separate payments, receipts, refunds, transfers and pending | rule tests; full-data reconciliation 9,488/9,488 | PASS |
| F3 | Monthly expenses, category distribution, cash flow; income forecast only when justified | analytics tests; browser 5, 17. The income forecast is NOT APPLICABLE (HW1's own condition is unmet, CF-01) | PASS (income forecast N/A) |
| F4 | Categories with a fallback | `test_keyword_rules_and_fallback` | PASS |
| F5 | Adjustable budgets with explainable advice | budget tests; browser 7 | PASS |
| F6 | Short-range estimate or a notice | `forecast_product` with an explicit result type; browser 8, 23, 30 | PASS. On Dataset A only a deterministic estimate is shown (no ML skill) |
| F7 | "Candidates for review", not fraud | labels; browser 9; new "why flagged" answer | PASS |
| F8 | Answers from valid summaries, no hallucination | assistant tests (incl. 14 new); browser 10, 11, 21, 24, 28, 29 | PASS |
| F9 | Deletion; no unnecessary sharing | deletion and retention tests; localhost-only server (new); browser 12, 22 | PASS |

## HW1 performance requirements (1.2.2)

| ID | Requirement | Evidence | Status |
|---|---|---|---|
| P1 | 100% of malformed files end in controlled failures | malformed-file tests incl. the overflow guards; a combined-range check for appended files (new) | PASS |
| P2 | Totals exactly equal independent references | 9,488/9,488 (re-run); fixtures | PASS |
| P3 | Macro-F1 against baselines | HW1 3.1.6 allows it only with real labels; none exist (CF-02) | NOT APPLICABLE |
| P4 | MAE and MASE against seasonal-naive / last-period, rolling chronological | E2 (rolling origin, one month ahead) | PASS |
| P5 | Prompt response on the final hardware | Container only: page first render 0.11–1.18 s, server start 0.73 s. HW1 gives no threshold, and the laptop was not measured | **PARTIAL** |

## HW1 constraints, design and risks

| ID | Status | Note |
|---|---|---|
| C1–C3, D1, A1, A2, W1, S1–S11 | PASS | `docs/requirements_traceability.md`. C2 ("local") is now also enforced at the network level (127.0.0.1) |
| R1, R2, R4–R8 | PASS | `reports/verification/risk_and_blockers_report.md` |
| R3 (validate on voluntary de-identified real cases when permissible) | **NOT TESTED** | Not performed; all data is synthetic. This must be disclosed as an open limitation |

## HW2 experiments (original, unchanged)

| Exp | Definition | Evidence that it is unchanged | Result | Status |
|---|---|---|---|---|
| E1 | Financial correctness | fixture values unchanged (only a doc-path note changed) | exact; full-data reconciliation 9,488/9,488 (a later strengthening) | PASS |
| E2 | Forecasting; split 2024-01..2025-12 / 2026-01..04 / 2026-05..07; keep a model only if it beats the best baseline on validation MAE and MASE | outputs and models only from commit `04e8c37`; `0849ff5` added binaries only | the rule **kept** GBR (validation MAE 26.554 vs MA3 42.507; test 27.194 / RMSE 71.399 / MASE 0.570). The later post-hoc E2-QG found that a zero forecast is better (validation 24.697) | PASS (as designed; interpret with E2-QG) |
| E3 | Per-account IF vs robust z; 1% injection; P@k, recall, ROC-AUC | outputs only from commit `04e8c37` | per-account IF **lost** to the baseline: P@k 0.008 vs 0.037; AUC 0.559 vs 0.581. Global IF (deviation D-07): 0.041 / 0.587. F1@k = P@k; FPR@k ≈ 1.0% (re-derived) | PASS (as designed; negative finding) |
| E4 | Fixed user tasks (HW1 3.2.6); completion and errors | original run in `0849ff5`: 12/12, 0 errors, mean 2.21 s, after 7 fix iterations | the extended scripted set is now 29/29. No human participants | PASS (scripted) |

## Supplementary experiments (not part of HW2; separate IDs)

| ID | Dataset | Result | Reproduced in this audit |
|---|---|---|---|
| E2-QG (post-hoc) | A | no model beats zero; R² < 0 | — (frozen) |
| E2-B | B, PersonaLedger, CC BY 4.0 | test MAE 971.34 vs 1,022.66 (−5.0%); 80% coverage 77.7% | **yes, exact** (`e2b_reproduction.json`) |
| E3-B | B, identity-theft labels | AUC 0.48–0.52 (chance) | — (frozen) |
| C1–C4 | C, controlled synthetic | pipeline validation only | — (frozen) |

## Citations

See `CITATION_VERIFICATION.md`.
* **Verified (index pages):** lesner2019, alhenshiri2026, liu2008, liu2012, breiman2001, chen2016, lundberg2017, Taylor & Letham, Hyndman & Koehler, Dataset A, Dataset B and its paper.
* **Unresolved:** `yang2026` and `[9]`.
