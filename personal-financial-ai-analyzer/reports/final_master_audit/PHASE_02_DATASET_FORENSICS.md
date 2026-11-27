# Phase 2: Dataset Forensics

Status: **COMPLETE**.

* **Dataset A** (original): identity verified and re-hashed, SHA-256 `b18c8359…7c17` (unchanged before and after this programme); 50,000,000 rows; full quality audit; licence CC BY-NC 4.0. Details: `DATASET_FORENSIC_REPORT.md`, `DATASET_MANIFEST.json`, `DATA_QUALITY_REPORT.json`.
* **Registry and suitability matrix:** `DATASET_REGISTRY.md`.

## Forecasting suitability matrix (measured)

| Property | Dataset A | Dataset B | Dataset C (structured users) |
|---|---|---|---|
| Account histories | 1M accounts, 20–92 transactions each | 22,018 users, ~1,350 transactions each over ~37 months | 200 users × 36 months |
| Zero months within a series' span | 45% (train) → 62% (validation and test) | 0% | 0% |
| Mean within-series lag-1 autocorrelation | −0.044 | −0.048 | AR(1) φ = 0.7 by construction |
| Between-series level differences | weak | strong (persona levels) | moderate |
| Labels | none (synthetic injection only) | identity-theft rows (`is_fraud`) | full ground truth |
| Merchant text | none | merchant names and types (LLM-generated) | categories |
| Verdict for next-month spending | **not suitable** (E2-QG) | **suitable for a level-aware model** (E2-B) | positive control only |
