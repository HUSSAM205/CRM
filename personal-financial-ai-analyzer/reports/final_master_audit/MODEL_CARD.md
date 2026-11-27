# Model Card (summary)

Full card: [`docs/MODEL_CARD.md`](../../docs/MODEL_CARD.md).

| Model | Quality-gate status | In the product |
|---|---|---|
| Forecast outlook (historical median + 80% interval) | deployed (deterministic, no learned weights) | yes: next-month typical spending |
| GBR (HW2 E2), GBR seasonal | **REJECTED** (do not beat the zero baseline) | record only |
| GBR extended (E2-QG) | **REJECTED** | no |
| Isolation Forest (global) | **PARTIAL** (operational, weak: F1@k 0.041) | yes: ranks review candidates |
| Robust z-score | PARTIAL | shown alongside |
| IF per account (HW2 5.5) | REJECTED for deployment | no |

Every deployed artifact has metadata (algorithm, hyperparameters, seed, dataset SHA-256, periods, row counts, metrics, feature schema, library versions, creation time) and loads in a fresh process, both with and without the dataset (M-06).
