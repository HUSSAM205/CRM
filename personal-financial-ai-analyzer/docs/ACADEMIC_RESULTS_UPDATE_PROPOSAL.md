# Academic Results Update Proposal

This is a proposal for the final academic report. It does **not** change the submitted HW1 or HW2 documents or the original experiments.

## 1. Keep unchanged (original HW2 experiments on Dataset A)

* **E1:** financial correctness, exact. Strengthened by a full-data reconciliation of 9,488/9,488 checks.
* **E2:** forecasting with the HW2 selection rule; GBR kept (validation MAE 26.554 vs MA3 42.507; test 27.194). Report it **as originally designed**, with the same split, baselines and metrics.
* **E3:** anomaly ranking with injected anomalies (1%, seed 42).
  * The HW2-specified method (per-account Isolation Forest) did **not** beat its robust z-score baseline: precision/recall@k 0.008 vs 0.037; ROC-AUC 0.559 vs 0.581.
  * The global Isolation Forest (a documented deviation, CF-16 / D-07) scored 0.041 and 0.587.
  * Report this honestly.
* **E4:** fixed user tasks, run as a scripted browser test, not with human participants.
  * The original 12 tasks: 12/12 completed, 0 errors, mean 2.21 s (run 03:58 UTC). This was the final of 7 iterations while script and app defects were being fixed (`EXPERIMENT_REGISTRY.md` U-01).
  * The later extended set: 24/24.

## 2. Add as clearly separate, later experiments (new IDs, own data and protocol)

| ID | Question | Dataset | Result | Status |
|---|---|---|---|---|
| E2-QG (post-hoc) | Does any model beat a zero / median forecast on A? | A | No: zero has validation MAE 24.70 vs GBR 26.55; R² < 0 for all models. The zero baseline was added after the E2 results were known | GBR not used in the product (HW2's E2 decision still stands) |
| E2-B | Can a lightweight model forecast continuous personal card spending? | B (PersonaLedger, CC BY 4.0) | Yes, modestly: test MAE 971.34 vs 1,022.66 (−5.0%, CI excludes 0); R² 0.23 | ACCEPTED, domain-guarded |
| E3-B | Do the HW2 anomaly features detect another person's spending day? | B identity-theft labels | No: AUC 0.48–0.52 | negative finding |
| C1–C4 | Is the pipeline itself correct and able to learn when signal exists? | C (controlled synthetic) | Totals exact (14,320/14,320); recurring P 0.986 / R 0.865; GBR beats baselines only on structured series; rule surfacing finds 82–100% of injected rule anomalies | pipeline validated (synthetic only) |

## 3. Suggested wording for the discussion

* Implementation completeness and scientific validity are separate questions.
* On the original synthetic benchmark (A), monthly spending has no learnable temporal structure (autocorrelation −0.044). There, the correct outcome is to reject ML forecasting and keep a deterministic reference.
* A positive control (C3) shows that the same pipeline learns when structure exists. A second public synthetic dataset (B) shows a small model gain that a user-level bootstrap distinguishes from zero: −1.1% MAE on validation, −5.0% on test.
* All datasets are synthetic, so **no real-world accuracy or fraud-detection claim is made**.

## 4. Do not claim

* That the new experiments were part of HW2.
* Real-world validity.
* That anomaly detection finds fraud.
* That Windows or laptop performance was measured. These remain open (`reports/final_master_audit/KNOWN_LIMITATIONS.md`).
