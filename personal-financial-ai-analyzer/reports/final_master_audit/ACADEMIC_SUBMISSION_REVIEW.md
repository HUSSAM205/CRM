# Academic Submission Review

* **Date:** 2026-11-27
* **Scope:** final academic review before submission. No application, architecture or feature changes were made.
* **Original submissions, read only and unmodified:**
  * `ST_HW1_Hussam_Aburahmah_2357138_2.pdf`, SHA-256 `2edba1b1…f439`;
  * `ST_HW2_Hussam_Aburahmah_2357138_1.pdf`, SHA-256 `09c50657…2d43`.
* **Code state reviewed:** verified at `09c1ce4`.
  * Fresh clone: 192 passed / 4 skipped (data-dependent).
  * Development run: 196 passed.
  * Source: `TEST_RESULTS.md`.

> **Verdict: NOT YET READY FOR SUBMISSION. It becomes ready once the report-level items in §11 are done.**
>
> The engineering evidence is sound and reproducible. What blocks submission is the written report:
> * HW1 has no bibliography;
> * HW2 Tables 9.1 and 9.2 are empty;
> * E2 and E3 need honest framing;
> * performance on the laptop and on Windows has never been measured.
>
> None of these needs new experiments, except the optional laptop benchmark.

---

## 1. HW1 requirements: is each one accurately represented?

Sources:
* HW1 text, extracted from the PDF;
* `docs/requirements_traceability.md`.

**Functional requirements (HW1 1.2.1)**

| ID | Status | Notes |
|---|---|---|
| F1 Read and validate CSVs | Accurate (PASS) | |
| F2 Separate transaction types before computing | Accurate (PASS) | |
| F3 Monthly totals, categories, cash flow | Accurate. Descriptive income only | HW1 conditions an income forecast on being "justified"; that condition is not met (CF-01). The report must say so explicitly. |
| F4 Categories with a fallback | Accurate (PASS) | |
| F5 Budgets | Accurate (PASS) | |
| F6 Short-range estimate or a notice | Accurate, but needs careful wording | On Dataset A, ML forecasting has no real skill (§6). The product shows the deterministic outlook there. The ML model is used only on Dataset B-like series. |
| F7 Anomalies as "candidates for review" | Accurate (PASS) | The wording never says fraud. Keep it that way in the report. |
| F8 Answers grounded in summaries | Accurate (PASS) | The assistant uses deterministic templates. No LLM. |
| F9 Deletion and no sharing | Accurate (PASS) | |

**Performance requirements (HW1 1.2.2)**

| ID | Status | Notes |
|---|---|---|
| P1 Controlled failures on malformed CSVs | PASS | Includes the overflow fixes (A-01, M-02). |
| P2 Totals exactly match references | PASS | Full-data reconciliation: 9,488/9,488. |
| P3 Macro-F1 classification | N/A, justified | HW1 3.1.6 allows macro-F1 "only with real labels", and none exist (CF-02). Do not report a macro-F1. |
| P4 MAE and MASE vs seasonal naive / last period, rolling chronological | PASS | Rolling origin, one month ahead (`docs/evaluation_methodology.md`). |
| P5 "Prompt" response on the final hardware | **PARTIAL** | HW1 gives no numeric threshold. The only timings come from the cloud container. The laptop was **never measured** (§8). |

**Constraints, design, architecture and risks**

| ID | Status | Notes |
|---|---|---|
| C1–C3, D1, A1, A2, W1, S1–S11 | Accurate | S7 was corrected in the final audit, when the missing date filter was added (A-02). |
| R1–R8 risks | Accurate, with one residual | R3 says "validate on voluntary de-identified test cases when permissible". **This was not done.** It must be listed as an open limitation, not as mitigated. |
| HW1 3.2.6 user tasks | Accurate | All are covered by E4 (§2). |

**HW1 document defects.** These cannot be fixed in the submitted file. Fix them in the final report:

1. **No bibliography.** The text contains unresolved LaTeX keys:
   * `cite lesner2019`
   * `cite alhenshiri2026`
   * `cite yang2026`
   * `liu2008,liu2012`
   * `cite breiman2001`
   * `chen2016`
   * `citelundberg2017`

   It also contains the bare markers `[1]` and `[9]`.
2. **§4.1 has an incomplete sentence:** "local size, hash, and version commit are."
3. Stray "text Environment impact" tokens, and section 2.5 is missing.
4. The figures on pages 8–11 are images. Check that they are legible in the final report.

## 2. HW2 experiments E1–E4: unchanged?

| Exp | Definition (HW2 §8.1, Tables 8.1–8.2) | Evidence that it is unchanged | Result to report |
|---|---|---|---|
| E1 | Financial correctness against reference values | `tests/fixtures/expected_financial_results.json`: only a documentation path note changed (financial_rules.md → FINANCIAL_RULES.md); no values changed | Exact: 0 mismatches. Full-data reconciliation 9,488/9,488 (a later strengthening; label it as such). |
| E2 | Forecasting with the original split and rule: train 2024-01..2025-12, validation 2026-01..04, test 2026-05..07. Keep a model only if it beats the best baseline on validation MAE and MASE | `reports/experiments/forecasting/`: a single commit, `04e8c37`. Artifacts for gbr and gbr_seasonal: `04e8c37`, plus `0849ff5`, which only added `model.joblib` binaries to the same version directories (no retraining) | Rule outcome: ETS, GBR and GBR seasonal are kept; GBR is selected. See §6. |
| E3 | Per-account Isolation Forest vs robust z-score; 1% injected anomalies; Precision@k, recall, ROC-AUC | `reports/experiments/anomaly/`: a single commit, `04e8c37` | The HW2-specified method **did not beat** its baseline. See §7. |
| E4 | Fixed user tasks (HW1 3.2.6); completion rate and error count | Original run in `0849ff5`: 2026-11-27T03:58:28Z | 12/12 completed, 0 errors, mean 2.21 s. This was the final of **7 iterations** while defects in the script and the app were being fixed (`EXPERIMENT_REGISTRY.md` U-01). The tasks were scripted with Playwright, **with no human participants**. The current file holds a later extended run of 24/24; report that separately. |

**Conclusion.** The definitions, split, metrics and selection rule of E1–E4 are unchanged. Neither the outputs nor the trained models were regenerated after the selection.

**Documented deviations from the HW2 plan.** Declare these in the report:
* The deployed app uses a **global** Isolation Forest, while HW2 5.5 specifies a per-account forest (CF-16, D-07). The per-account version is the one evaluated in E3.
* Training used aggregate panels of 20,000 eligible series, not a saved raw-row subset (HW2 6.3).
* Every run was on a cloud container, not the "student laptop" named in HW2 6.1.

## 3. Original vs supplementary results

| Category | Experiments | Dataset | Where to put it in the report |
|---|---|---|---|
| **Original (HW2)** | E1, E2, E3, E4 | A: FreeFinancialTransactions50M | Chapter 9, Tables 9.1 and 9.2 |
| Supplementary, post-hoc | E2-QG: zero and median references on the E2 test | A | Separate chapter; label it "post-hoc" |
| Supplementary, new data | E2-B (forecasting), E3-B (identity theft) | B: PersonaLedger | Separate chapter, with its own protocol |
| Supplementary, controlled | C1–C4 | C: generated by this project | Separate chapter; "pipeline validation only" |
| Engineering extensions | Advisor, Assistant extension, full-data reconciliation, extended E4 (24 tasks) | — | Implementation chapter or appendix, not results |

A **"PersonalLedger" dataset does not exist** in this repository. The dataset is called **PersonaLedger**. Use that exact name.

## 4. No synthetic experiment presented as real-world validation

All three datasets are synthetic:
* A is synthetic according to its provider;
* B is LLM-generated synthetic data (Capital One Research);
* C was generated by this project.

Repository wording was checked:
* `docs/ACADEMIC_RESULTS_UPDATE_PROPOSAL.md` §3–4 and `KNOWN_LIMITATIONS.md` both state "no real-world accuracy or fraud-detection claim".
* The proposal's C1–C4 row says "pipeline validated (synthetic only)".

**Required in the report:** one sentence in the abstract, and one in the conclusion, saying that every quantitative result comes from synthetic data and that no real-world validation was performed (R3 was not done).

## 5. Dataset citations, licences and attribution

| Item | Verified | Status / action |
|---|---|---|
| Dataset A licence | CC BY-NC 4.0, from the dataset card and `PROVENANCE.json` | OK. **Non-commercial:** state this, and make no commercial-use claim. |
| Dataset A citation | HW2 ref [1] (ziadatalabs, Hugging Face) | OK. Add the access date and the file hash, which also fixes the incomplete HW1 §4.1 sentence. |
| Dataset B licence | CC BY 4.0. Hugging Face API card shows `license: cc-by-4.0`, not gated, revision `c90078ae4ac47e582c9263579466a905fa4adfab` | OK. Attribution is required, see `data/samples/ATTRIBUTION.md`. |
| Dataset B citation | The card lists the authors: Yuan, Farnan, Tesliuc, Bergman, Wu, Liu, Liu, Montgomery, Nguyen, Bruss, Huang. The card's citation block and paper link are **empty** | **Cite the Hugging Face dataset card with its revision.** An arXiv paper (2601.03149) appeared in search results, but it **could not be verified**: arXiv was blocked from this environment. Cite it only after you have checked it yourself. |
| Dataset C | Generated by `scripts/research/` in this repository | Cite as "generated by the author". No licence issue. |
| HW2 references [1]–[7] | Liu, Ting & Zhou (ICDM 2008); Hyndman & Koehler (IJF 22(4), 2006); Taylor & Letham (Am. Stat. 72(1), 2018); Breiman (ML 45, 2001); Chen & Guestrin (KDD 2016); Pedregosa et al. (JMLR 12, 2011) | These are well-known, correct references. Keep them. |
| HW1 keys | breiman2001, chen2016, liu2008 resolve to the HW2 references. lundberg2017 is the well-known SHAP paper (NeurIPS 2017). **lesner2019, alhenshiri2026, yang2026 and liu2012 could not be verified** | Verify each against the source you actually read, or remove the claim. Do not invent entries. |
| HW1 `[9]` (rolling validation) | Unresolved | Most likely Hyndman & Koehler 2006 or a forecasting textbook. Confirm which one you meant. |
| Software | scikit-learn [7], Polars, PyArrow, Streamlit, Playwright | Add the versions from `requirements*.txt` or the environment file. |

## 6. Forecasting: limitations and why the HW2 model was rejected

**What HW2's rule decided.** GBR beat every HW2 baseline on validation:
* GBR: MAE 26.554, MASE 0.551;
* best baseline, MA3: MAE 42.507, MASE 0.845.

So **the rule kept GBR**. On test, GBR scored MAE 27.194, RMSE 71.399, MASE 0.570. That is E2's result. Report it exactly as designed.

**Why the product does not use it (post-hoc, E2-QG):**
* **A zero forecast beats GBR.** On validation the zero forecast scored MAE 24.697 and MASE 0.511, against GBR's 26.554. On test it scored 25.374 and 0.532, against GBR's 27.194.
* 62.1% of test months are zero.
* Every model has R² < 0.
* The mean autocorrelation within a series is −0.044 at both lag 1 and lag 12.

So monthly spending in Dataset A has no learnable temporal structure. GBR "won" because the HW2 baselines carry past spikes forward, while GBR shrinks its forecasts towards zero.

**Honest framing.** The zero and median references were **not** HW2 baselines. They were added after the E2 results were known (from the diagnostic at 03:33 UTC). E2-QG is therefore exploratory and post-hoc, not a confirmatory pre-registered test. The project docs were corrected to say this.

**Other limitations to state:**
* The ETS fits produced 1,692 convergence warnings.
* MASE excludes series whose scale is zero; those exclusions are counted.
* The robustness runs vary a little: GBR test MAE 25.24 with seed 43, 27.721 with seed 44, 26.796 on an account-disjoint split.
* The E2-B gain on Dataset B is small: −1.1% MAE on validation, −5.0% on test. A user-level bootstrap distinguishes it from zero, but the gate had no minimum effect size, and the result comes from synthetic data.
* The product uses the E2-B model only for series with at least 12 months of history and no zero months (D-24).

## 7. Anomaly detection: limitations, especially identity theft

**E3 as HW2 specified it** (1% injection, seed 42, k = 241):

| Model | P@k = R@k | ROC-AUC | AUC: amount-type injections | AUC: hour-type | AUC: category-type |
|---|---|---|---|---|---|
| Robust z-score (baseline) | 0.0373 | 0.5811 | 0.804 | 0.534 | 0.428 |
| **IF per account (HW2 5.5)** | **0.0083** | **0.5595** | 0.636 | 0.552 | 0.499 |
| IF global (deployed; deviation D-07) | 0.0415 | 0.5875 | 0.751 | 0.516 | 0.509 |

**What the table shows:**
* The HW2-specified method lost to its simple baseline.
* The global forest is only slightly better than the baseline, and it is a deviation from the plan.
* All AUCs are near chance (0.5), except for injected amount outliers.
* A positive control (anomalies ×1000) reaches AUC 0.9988. So the pipeline works, but the injected anomalies are subtle and the features are weak.

**Identity theft (E3-B, Dataset B labels).** ROC-AUC is 0.477–0.520, which is chance level. The HW2 features (amount, hour, category) **cannot** detect a different person's spending day. Rule-based surfacing in C4 finds 82–100% of injected rule anomalies, but that result is circular: the generator was built with those same anomaly types.

**Required wording:** "unusual-transaction review candidates". Never "fraud detection", "fraud alerts" or "identity-theft detection". No supervised fraud model was trained, because there are no real fraud labels.

## 8. Windows and laptop benchmark evidence

* `reports/laptop_benchmark.json` **does not exist**.
* No Windows run exists anywhere in the repository (`docs/WINDOWS_INSTALLATION.md`: "NOT TESTED").
* The target specification (Intel Core i7-1355U, 16 GB) is **user-reported** and was not measured.
* **Nothing can be added to the report** about the laptop or Windows until you run `benchmark.bat` (and steps 1–6) on the laptop yourself.
* Before you read the results, define a P5 threshold in the report (for example, server-side page render under 2 s).
* The container timings (setup 23–30 s; E4 mean 2.21 s) may be reported only as "cloud container, Linux". Never present them as laptop results.

## 9. Unsupported or overstated claims

**Fixed in this review** (uncommitted working-tree edits):

| File | Original claim | Problem | Correction |
|---|---|---|---|
| `README.md` (results table) | "Dataset A (HW2): GBR **rejected** by the quality gate" | Implies that HW2 rejected GBR, but the HW2 rule kept it | Now says that HW2 kept GBR and that a later post-hoc check led to it not being used in the product |
| `docs/FORECASTING.md` §2 | Protocol "fixed before any test number of this experiment existed" | Literally true, but the zero-forecast test numbers were already known | Now labelled "post-hoc analysis, not a confirmatory test" |
| `docs/REPRODUCIBILITY.md` | "pre-registered protocol" | Same issue | "post-hoc analysis" |
| `docs/ACADEMIC_RESULTS_UPDATE_PROPOSAL.md` | "small but significant"; the E3 line hid that per-account IF lost; E4 lacked the original 12/12 and its iterations; E2-QG not labelled post-hoc | Overstatement and omission | All four corrected |
| `reports/final_master_audit/FINAL_MASTER_AUDIT.md` Gate D | "A: AUC 0.80 by type" | 0.80 is the robust z-score, not the IF | Gives all three methods |
| `docs/WINDOWS_INSTALLATION.md` | Hardware specification stated as fact; "closes HW1 P5"; "Linux reference: 26 s" | Unmeasured specification; P5 has no threshold; a single value for a range | Marked user-reported; P5 threshold guidance added; 23–30 s |
| `reports/final_evidence/results_tables.md` and `facts.json` | "125 passed", "15/15", "6/6" | Stale | Regenerated: 196 passed, 24/24, 8/8 |
| `PHASE_13_ACADEMIC_TRACEABILITY.md` | Did not name the deviations from HW2 | Omission | Deviations listed |

**Still unsupported. Fix these in the final report:**

1. Any HW1 claim that rests on the unverified keys lesner2019, alhenshiri2026, yang2026 or liu2012.
2. HW1 P5 "prompt response on the final hardware": no measurement exists.
3. HW1 R3 "validate on de-identified real cases": not done.
4. HW2 6.1 "Student laptop" as the hardware: all runs were on a cloud container.
5. HW2 Tables 9.1 and 9.2 "to be filled": still empty in the submitted file. Fill them in the final report with the values in §6 and §7.
6. Any statement that E4 measured usability: it was scripted, with no human participants. It measures functional completion only.
7. The PersonaLedger arXiv paper: not verified.

## 10. Proposed structure of the final report

1. **Abstract:** state clearly that all data is synthetic, ML forecasting failed on A, anomaly detection is weak, and no fraud claim is made.
2. **Introduction and problem statement.** Taken from HW1 chapters 1–2, with section 2.5 fixed.
3. **Related work.** The HW1 literature, with a **verified bibliography**.
4. **Requirements:** F1–F9, P1–P5 (P3 N/A, P5 PARTIAL), constraints, and R1–R8 (R3 open).
5. **Data:**
   * Dataset A: licence, hash, access date, synthetic nature; this fixes the HW1 §4.1 sentence.
   * Preprocessing, and the decision never to use `balance_after` (D-03).
6. **System design and implementation.** Architecture and pages, with Advisor and Assistant as engineering extensions.
7. **Experimental design.** HW2 chapter 8, unchanged: E1–E4, the split, the metrics, the selection rule.
8. **Results of the original experiments:**
   * Table 9.1 (E2): baselines, ETS, GBR and GBR seasonal on validation and test.
   * Table 9.2 (E3): the three models, with per-type AUCs.
   * E1 exactness.
   * E4: 12/12 from the original run, with its iteration history.
9. **Supplementary experiments (not part of HW2).** Each with its own protocol, labelled post-hoc or new:
   * E2-QG;
   * E2-B and E3-B on PersonaLedger (CC BY 4.0, with attribution);
   * C1–C4 on controlled synthetic data.
10. **Discussion:**
    * why GBR was kept by the rule but not used in the product;
    * why the per-account IF lost;
    * identity theft at chance level;
    * implementation completeness vs scientific validity.
11. **Limitations and deviations:**
    * synthetic-only data;
    * global vs per-account IF;
    * cloud container instead of the laptop;
    * panel-based training;
    * no human-participant evaluation;
    * no real labels.
12. **Performance (P5):** either the laptop benchmark with its predefined threshold, or an explicit "not measured".
13. **Conclusion and future work:** real de-identified validation (R3), a labelled category set, and human-participant evaluation.
14. **References.** Complete, consistent style, every entry verified.
15. **Appendix:** reproducibility (commit hash, commands, environment), AI-assistance disclosure if your course requires one, and the traceability matrix.

## 11. Exactly what you need to update before submission

**Required:**

1. **Build a verified bibliography** for all HW1 citation keys and the bare `[1]` and `[9]`. Remove any claim whose source you cannot confirm.
2. **Fill Tables 9.1 and 9.2** with the numbers in §6 and §7. Report test values once, and say that the selection was made on validation.
3. **Report E2 honestly:** the rule kept GBR, and then the post-hoc E2-QG showed no real skill.
4. **Report E3 honestly:** the per-account IF lost to the z-score, and the global IF is a declared deviation.
5. **Report E4 honestly:** 12/12 from the original run, after 7 fix iterations; scripted, with no human participants.
6. **Put the supplementary experiments in their own chapter** (§3). Never mix them into the Chapter 9 tables.
7. **State that all data is synthetic and there is no real-world validation**, in the abstract, the discussion and the conclusion.
8. **Correct the dataset name** to PersonaLedger, cite its Hugging Face card with the revision, and add CC BY 4.0 attribution. Cite the arXiv paper only if you verify it yourself.
9. **State the Dataset A licence (CC BY-NC 4.0)**, and complete the HW1 §4.1 sentence with the file size, the SHA-256 and the access date.
10. **P5:** run `benchmark.bat` on your laptop with a threshold defined beforehand. Otherwise, state "not measured on the target laptop".
11. **Declare the deviations:** global IF (D-07), panel-based training, cloud hardware, and R3 not done.
12. **Fix the HW1 typesetting defects** in the final text: the stray tokens, the missing section 2.5, and the legibility of the figures.

**Recommended:**

13. Add the software versions and an appendix with the reproducibility commit.
14. Add an AI-assistance disclosure if your course policy requires one.
15. Commit the doc corrections from this review, if you accept them. They are currently uncommitted.

## 12. Submission checklist

| # | Item | State |
|---|---|---|
| 1 | Original HW1 and HW2 PDFs unmodified (hashes match) | ✅ |
| 2 | E1–E4 definitions, split, metrics and rule unchanged | ✅ |
| 3 | E1–E3 outputs and models not regenerated after selection | ✅ (git: `04e8c37`; `0849ff5` added binaries only) |
| 4 | Code reproducible from a fresh clone | ✅ (192 passed / 4 skipped, data-dependent) |
| 5 | Tables 9.1 and 9.2 filled in the final report | ❌ to do |
| 6 | E2 framed as "kept by the rule, post-hoc no real skill" | ❌ to do in the report (repository docs fixed) |
| 7 | E3 framed as "per-account IF lost to the baseline" | ❌ to do in the report (proposal fixed) |
| 8 | E4 reported as the original 12/12, scripted, with its iteration history | ❌ to do in the report |
| 9 | Supplementary experiments in a separate chapter | ❌ to do |
| 10 | Synthetic-only disclaimer | ❌ to do in the report (repository docs ✅) |
| 11 | No fraud or identity-theft detection claim | ✅ in the app and docs; check the report text |
| 12 | Complete, verified bibliography | ❌ HW1 has none |
| 13 | Dataset A licence (NC) and citation | ⚠️ add the licence and access date |
| 14 | Dataset B: correct name, Hugging Face card citation, CC BY attribution | ⚠️ to do; arXiv unverified |
| 15 | P5: laptop measurement with a predefined threshold, or "not measured" | ❌ no evidence |
| 16 | Windows installation tested | ❌ NOT TESTED; disclose this |
| 17 | Deviations declared (D-07, panels, hardware, R3) | ❌ to do in the report |
| 18 | No datasets, credentials or personal data in Git | ✅ (repository completeness and `data/supplementary` guard tests) |
| 19 | HW1 typesetting defects fixed in the final text | ❌ to do |
| 20 | Doc corrections from this review committed | ⚠️ uncommitted, awaiting your approval |

## 13. Verdict

**NOT YET READY FOR SUBMISSION.**

**What is ready:**
* Every HW1 functional requirement is implemented with evidence.
* E1–E4 are intact and reproducible.
* The negative findings are preserved.
* Licences are known for every dataset.

**What blocks submission** is the report itself:
* the missing bibliography;
* the empty result tables;
* the framing of E2, E3 and E4;
* the separation of supplementary work;
* the disclosure that P5 and Windows were never measured.

Once checklist items 5–17 and 19 are done, the submission is **READY WITH LIMITATIONS**:
* synthetic data only;
* ML forecasting is not effective on the original dataset;
* anomaly ranking is weak, and identity theft is not detectable;
* P5 is partial unless you measure the laptop.

No experimental results, citations or hardware measurements were fabricated for this review.
