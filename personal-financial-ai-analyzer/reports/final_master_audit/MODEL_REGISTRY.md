# Model and Experiment Registry

Each experiment is listed, including rejected ones. Machine-readable registry: `artifacts/metadata/model_registry.json`. Model card: `docs/MODEL_CARD.md`.

| Model / experiment | Dataset | Target | Features | Config / seed | Split | Key metric | Train time | Size | Decision | Reason |
|---|---|---|---|---|---|---|---|---|---|---|
| naive, seasonal naive, MA3 (E2) | A | next-month spending | — | — | HW2 | test MAE 42.945 / 51.602 / 39.259 | — | — | baselines | — |
| ETS(A,N,N) (E2) | A | same | series | statsmodels | HW2 | test MAE 40.593 | 82.7 s validation | not saved | not used | worse than the median; per-series fitting |
| GBR, GBR seasonal (E2) | A | same | lag 1–3, rolling mean 6, month (+ lag 12) | depth 3, lr 0.05, 100 iterations, seed 42 | HW2 | test 27.194 / 26.232 | 1.5 s | 111 kB / 112 kB | kept by the HW2 rule; **REJECTED** by E2-QG | zero forecast better (25.374) |
| GBR extended (E2-QG) | A | same | 11 past-only | depth 6, lr 0.1, 300 iterations | HW2 | validation 25.843 vs zero 24.697 | 5.6 s | not saved | **REJECTED** | predicts 0 after the refit; no signal |
| historical-median outlook | A | same | expanding median | — | HW2 | test 26.546; 80% interval coverage 81.9% | — | metadata only | **DEPLOYED** (fallback) | best data-dependent baseline |
| **GBR scale-free (E2-B)** | B | next-month user spending | 8 ratio features | depth 3, lr 0.05, 300 iterations, seed 42 | train ≤ 2026-06, validation 2026-07..12, test 2027-01..06 | test 971.34 vs 1,022.66; CI excludes 0; R² 0.232 | 1.6 s | 320 kB | **ACCEPTED, DEPLOYED** (in-domain only) | passes the pre-registered gate |
| robust z, IF per account, IF global (E3) | A | injected anomalies | 5 account-relative | 100 trees, seed 42 | test period | AUC 0.581 / 0.559 / 0.587 | 226.9 s (9 runs) | IF 1.4 MB | IF global **DEPLOYED** (PARTIAL); per-account not deployed | weak; cannot score unseen accounts |
| robust z, IF 5 features, IF 7 features (E3-B) | B identity theft | thief rows | 5 / 7 | seeds 42–44 | 5,000 sequences per run | AUC 0.488 / 0.477 / 0.520 | 11.6 s total | not saved | **REJECTED** for this task | chance level |
| GBR (E2 config) on C3 | C | dining spending | HW2 seasonal | as E2 | months 12–23 / 24–29 / 30–35 | structured: 674 vs 781 (validation) | <1 s | not saved | positive control | — |

**Dataset hashes:** A `b18c8359…`; B `8ec0979c…` and `d68c03e8…`.

**Software:** Python 3.12.3, scikit-learn 1.9.1, statsmodels 0.15.0, polars 2.2.0 (`requirements-lock.txt`).
