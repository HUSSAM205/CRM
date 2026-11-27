# Academic Requirements Report

Verified 2026-11-27.

| Item | Result | Status |
|---|---|---|
| HW1 located and read | Session upload `ST_HW1_Hussam_Aburahmah_2357138_2.pdf`, all 18 pages read as images (tables, WBS, PN, Gantt, risk matrix, architecture and flow figures inspected) | PASS |
| HW2 located and read | Session upload `ST_HW2_Hussam_Aburahmah_2357138_1.pdf`, all 16 pages read (Tables 4.1, 4.2, 6.1, 7.1, 8.1, 8.2, 9.1, 9.2, 10.1) | PASS |
| Requirements extracted | 69 traceability rows covering F1–F9, P1–P5, constraints and design, S1–S12, dataset DS1–DS8, and HW2 methodology, experiments and tests | PASS |
| HW1 and HW2 compared | HW2 chapter 4 restates HW1 chapter 4. HW2 chapters 5–10 narrow HW1's design. HW1 F1–F9, performance requirements, risks and subsystems are kept as binding | PASS |
| Conflicts identified | 16 (CF-01…CF-16), each with a resolution. None silently dropped | PASS |
| Requirements mapped to implementation work | Every row has an implementation location (actual or planned) and a planned test | PASS |
| Requirements not implemented | CF-01 income forecast (HW1's own condition "when justified" is unmet: no salary labels). CF-02 macro-F1 classifier (no labeled descriptions; HW1 3.1.6 makes it conditional on real labels; HW2 5.3 rules it out) | Justified N/A |
| Citations | Only HW2 references [1]–[7] are reused. HW1's unrendered keys (lesner2019, alhenshiri2026, yang2026, lundberg2017) are **not** reused, because they could not be verified | Recorded |
| HW documents modified | No. The PDFs are not copied into the repository and are untouched | PASS |

Implementation status per requirement: `docs/requirements_traceability.md`. At this gate the tally is PASS 15 · PARTIAL 22 · NOT TESTED 31 · N/A 1. Most of the NOT TESTED rows are model, app and experiment work, which was gated until now.
