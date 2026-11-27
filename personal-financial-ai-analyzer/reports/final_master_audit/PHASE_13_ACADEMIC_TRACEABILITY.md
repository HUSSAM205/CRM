# Phase 13: Academic Traceability

Status: **PARTIAL** (HW1 P5 is not measurable here).

## HW1 / HW2: 69 rows (`docs/requirements_traceability.md`)

**67 PASS, 1 PARTIAL (P5: responsiveness on the final hardware), 1 N/A (P3: macro-F1; no labelled descriptions), 0 FAIL.**

* All 9 functional requirements F1–F9: PASS.
* HW2 methodology preserved:
  * E2 frozen, with the same split, baselines (naive, seasonal naive, MA3), ETS, GBR, MAE/RMSE/MASE and rolling origin;
  * E3 with Isolation Forest vs robust z on 0.5/1/2% injections and 3 seeds;
  * median-of-3 budgets and 80%/100% alerts;
  * the 5 fixed assistant intents;
  * seed 42 and saved models.
* E1 (exact financial calculations), E2, E3 and E4 (fixed tasks) all have evidence.

## Product enhancements: NOT part of HW1/HW2

These are listed separately: Advisor (goals, emergency fund, scenarios, affordability, recommendations), the extended assistant intents, Settings, Dataset B and E2-B, E3-B, Dataset C, E2-QG.

They are traced in `REQUIREMENTS_TRACEABILITY.md` §2 (40 items: 38 PASS, 1 PARTIAL, 1 NOT TESTED). Their presentation in the academic report is covered by `docs/ACADEMIC_RESULTS_UPDATE_PROPOSAL.md`.
