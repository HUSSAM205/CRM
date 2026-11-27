# Candidate Dataset Assessment (master audit 3, Phase 1)

**Rule applied.** A dataset is adopted only if its source, licence and schema are verified, and it legitimately represents what a feature needs.

**Network note.** openml.org, archive.ics.uci.edu and ieee-dataport.org are **blocked** by this environment's proxy (HTTP 000, 2026-11-27). Their schemas therefore could not be inspected first-hand. Licence facts below come from search-engine index pages and are marked as such.

| Candidate | Source verified | Licence | Accessible here | What it represents | Decision | Reason |
|---|---|---|---|---|---|---|
| **A: FreeFinancialTransactions50M** | Yes. HF API, revision `98cf38f9…`, LFS SHA-256 `b18c8359…7c17` matches the local file | CC BY-NC 4.0 (dataset card) | Yes | Synthetic account transactions: 50,000,000 rows × 9 columns, 1,000,000 accounts, 1,594,749,644 bytes | **KEPT, unchanged (original HW2 dataset)** | `scripts/verify_dataset.py`: OVERALL PASS, re-run in this audit |
| **B: PersonaLedger** | Yes. HF API, revision `c90078ae4ac47e582c9263579466a905fa4adfab` is the live head; both file SHA-256s match the LFS hashes | CC BY 4.0 (card `license: cc-by-4.0`, not gated) | Yes | Synthetic (LLM plus rules) personal card transactions; identity-theft labels | **KEPT, supplementary and isolated** | `scripts/download_supplementary.py`: PASS ×2, re-run in this audit. The correct name is **PersonaLedger** ("PersonalLedger" does not exist) |
| OpenML 43627 ("credit-card fraud") | **No.** The dataset page could not be opened, and no index page for ID 43627 was found. `docs/DATASET_REGISTRY.md` (master audit 2) identified it as a mirror of the ULB credit-card fraud set; that identification was **not** re-verified here | OpenML's general policy is CC-BY, but the per-dataset licence is unknown | No | Unknown. Commonly mirrored credit-card fraud sets are PCA-anonymised card transactions with fraud labels, not personal ledgers | **REJECTED** | Origin and licence not verifiable; schema not inspectable. The rule says reject when unclear |
| UCI Wholesale Customers (ID 292) | Partly (index): UCI page, Cardoso (2013), doi:10.24432/C5030X | CC BY 4.0 (UCI page, via index) | No | 440 **wholesale business clients**: annual spending in 6 product groups, channel and region | **REJECTED** | Business aggregate data, no dates, no transactions. It cannot represent personal financial histories, and using it would misrepresent the domain |
| IEEE DataPort "Daily Expense Prediction" | Partly (index): DOI 10.21227/xt6z-bc28 | Not verified (DataPort terms; some content needs a subscription) | No | 1,000 **synthetic** expense records (amount in INR, category, payment method, description) | **REJECTED** | Licence unverified, access may need an institutional login, and the data is very small and synthetic. It would add no validation value beyond Dataset C |

**Conclusion.** No additional dataset is adopted. The isolated dataset architecture is unchanged:

| Role | Dataset or location |
|---|---|
| Original academic | A |
| Supplementary | B |
| Controlled synthetic | C, generated |
| Product demos | `data/samples/` |
| User uploads | session memory only |

Each experiment names its dataset (`docs/DATASET_REGISTRY.md`, `EXPERIMENT_REGISTRY.md`).
