# Evidence Audit

Every claim in the earlier final documents was checked against a primary source (a raw file, log or re-execution).

| Earlier claim | Re-checked by | Outcome |
|---|---|---|
| Dataset identity (size, SHA, commit) | Live HF headers plus local SHA | **Confirmed** |
| 50M rows accounted for; totals exact | Independent PyArrow reconciliation over the full file (54/54) | **Confirmed** |
| Ledger 49M/49M | `ledger_semantics.json` (rerun not required: deterministic script, inputs unchanged) | Accepted |
| Forecasting and anomaly metrics | Fresh-process recomputation; |Δ| = 0.0 for all | **Confirmed** |
| "GBR improves on baselines" | Recomputed, with the zero and median baselines and the full population | **True under HW2's rule, but no predictive skill** (zero is better). It was already stated in `docs/final_results.md` and is strengthened here (F-1..F-5) |
| Artifacts load and reproduce | `verify_artifacts.py`, exit 0 | **Confirmed** |
| Determinism and resume | 3 partitions deleted and resumed; 9/9 content-identical | **Confirmed** (A-07 corrected the audit method) |
| "118 tests pass" | Re-run | Superseded: 124 passed now (new regression tests) |
| "UX 12/12" | Re-run with 3 extra tasks | 15/15 (after harness fix A-10) |
| **"27/27 acceptance PASS"** (`reports/final_validation_report.md`) | Fresh clone | **Overstated.** A clean clone failed entirely (A-08). The S7 date filter was missing (A-02). Malformed input could crash the validator (A-01). |
| Traceability rows S7 and P1 = PASS | Code inspection plus a test | **Were wrong.** Both are corrected and annotated in `docs/requirements_traceability.md` |
| Windows install | — | Still NOT TESTED (it was never claimed as tested) |

## Evidence files produced by this audit

* `reconciliation.json`, `panel_lifespan_check.json`, `training_audit.json`;
* `inference_performance.json`, `assistant_probe.txt`, `pip_audit.txt`, `static_security_scan.txt`;
* `dataset_immutability.txt`, `audit_start_checkpoint.txt`;
* `freshclone_before_fix/`, `freshclone3_after_fix/`;
* logs under `logs/execution/audit_*.log` and `logs/testing/pytest_20261127T052933Z.log`.

No screenshot, metric or timing in this package was produced by hand.
