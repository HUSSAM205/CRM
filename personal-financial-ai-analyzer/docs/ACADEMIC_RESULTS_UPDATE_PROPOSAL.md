# Academic Results Update Proposal

This is a proposal for the final academic report. It does **not** change the submitted HW1 or HW2 documents or the original experiments.

## 1. Keep unchanged (original HW2 experiments on Dataset A)

* **E1:** financial correctness, exact. Strengthened by a full-data reconciliation of 9,488/9,488 checks.
* **E2:** forecasting with the HW2 selection rule; GBR kept (validation MAE 26.554 vs MA3 42.507; test 27.194). Report it **as originally designed**, with the same split, baselines and metrics.
* **E3:** anomaly ranking with injected anomalies (AUC 0.56–0.59; F1@k ≤ 0.041).
* **E4:** fixed user tasks: 24/24 real-browser tasks; originally 12 HW2 tasks.

## 2. Add as clearly separate, later experiments (new IDs, own data and protocol)

| ID | Question | Dataset | Result | Status |
|---|---|---|---|---|
| E2-QG | Does any model beat a zero / median forecast on A? | A | No: zero has validation MAE 24.70 vs GBR 26.55; R² < 0 for all models | GBR REJECTED |
| E2-B | Can a lightweight model forecast continuous personal card spending? | B (PersonaLedger, CC BY 4.0) | Yes, modestly: test MAE 971.34 vs 1,022.66 (−5.0%, CI excludes 0); R² 0.23 | ACCEPTED, domain-guarded |
| E3-B | Do the HW2 anomaly features detect another person's spending day? | B identity-theft labels | No: AUC 0.48–0.52 | negative finding |
| C1–C4 | Is the pipeline itself correct and able to learn when signal exists? | C (controlled synthetic) | Totals exact (14,320/14,320); recurring P 0.986 / R 0.865; GBR beats baselines only on structured series; rule surfacing finds 82–100% of injected rule anomalies | pipeline validated (synthetic only) |

## 3. Suggested wording for the discussion

* Implementation completeness and scientific validity are separate questions.
* On the original synthetic benchmark (A), monthly spending has no learnable temporal structure (autocorrelation −0.044). There, the correct outcome is to reject ML forecasting and keep a deterministic reference.
* A positive control (C3) shows that the same pipeline learns when structure exists. A second public synthetic dataset (B) supports a small but significant model gain.
* All datasets are synthetic, so **no real-world accuracy or fraud-detection claim is made**.

## 4. Do not claim

* That the new experiments were part of HW2.
* Real-world validity.
* That anomaly detection finds fraud.
* That Windows or laptop performance was measured. These remain open (`reports/final_master_audit/KNOWN_LIMITATIONS.md`).
