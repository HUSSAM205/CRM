# Phase 1: Requirements and Architecture Audit

Status: **COMPLETE**.

**Sources:** HW1 (`ST_HW1_Hussam_Aburahmah_2357138_2.pdf`, 18 pages) and HW2 (`ST_HW2_Hussam_Aburahmah_2357138_1.pdf`, 16 pages). Both are summarised page by page in `docs/academic_source_analysis.md`. Conflicts between them are recorded in `docs/requirements_conflicts.md` (CF-01..CF-16; both references are kept).

**Traceability:**
* `docs/requirements_traceability.md` maps each requirement to code, tests and evidence: 69 rows, of which 67 PASS, 1 PARTIAL (P5) and 1 N/A (P3).
* The product requirements of the master programme are traced separately in `PHASE_13_ACADEMIC_TRACEABILITY.md`. They are never mixed with the HW rows.

**Gaps found against the programme** (listed in `BASELINE_STATE.md`):

| Priority | Gap | Phase where closed |
|---|---|---|
| P1 | Uploads in currencies outside the dataset's 6 (e.g. TRY) rejected (M-12) | 6 |
| P1 | No forecasting model validated anywhere; only "not effective" on Dataset A | 3–4 (Dataset B, E2-B) |
| P2 | Rule-flagged unusual transactions hidden by the ranking (M-14) | 5 |
| P2 | Unknown category answered with total spending (M-15) | 8 |
| P2 | Advisor: no essential/non-essential profile, fixed emergency fund, no goal editing, limited scenarios | 7 |
| P2 | Assistant: relative months, largest category, recurring, remaining budget, reliability, clarification, other-account refusal, context display missing | 8 |
| P3 | Forecast ranges truncated (M-13); no laptop benchmark procedure; no dataset registry or licence register | 11, 12, 14 |

**Architecture:** unchanged (Streamlit + `src/` library). New modules: `src/models/forecasting/scale_free.py`, product routing `forecast_product`, `src/assistant` intents, and `scripts/research/*`. See `docs/ARCHITECTURE.md`.
