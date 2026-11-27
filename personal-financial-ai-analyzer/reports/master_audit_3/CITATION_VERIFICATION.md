# Citation Verification (master audit 3, Phase 1)

**Method.** Direct access to Crossref, arXiv, OpenAlex and Semantic Scholar is blocked by this environment's network proxy: every request returned HTTP 000 (tunnel refused) on 2026-11-27.

The entries below were therefore checked with a web search engine. They are marked:
* **Verified (index)**: the publisher's or an indexing page (DBLP, NeurIPS proceedings, AAAI OJS, journal site) was returned with matching author, title, venue and year. The full text was **not** read here.
* **Unresolved**: no matching record was found. The student must supply the source or remove the claim.

Nothing was invented. The submitted HW1 file was not modified. This file is the input for the final report's bibliography.

## HW1 citation keys (HW1 §1.3.2 and §3.1.6)

| Key in HW1 | Claim in HW1 | Verified record | Status |
|---|---|---|---|
| `lesner2019` | Large-scale customised transaction classification; personalised context | C. Lesner, A. Ran, M. Rukonic, W. Wang. "Large Scale Personalized Categorization of Financial Transactions". *Proceedings of the AAAI Conference on Artificial Intelligence* 33 (IAAI track), pp. 9365–9372, 2019. doi:10.1609/aaai.v33i01.33019365 | Verified (index). Note: the paper is about **small-business bookkeeping** categories, so word the claim accordingly. The author order differs between the AAAI and AI Magazine versions; use the AAAI proceedings version. |
| `alhenshiri2026` | Classification of transaction descriptions from natural text | A. Alhenshiri et al. "An Intelligent System for Semantic Classification of Personal Expenses from Transaction Descriptions". *International Journal of Engineering & Information Technology (IJEIT)* 14(2), 2026. doi:10.36602/ijeit.v14i2.609 | Verified (index). Confirm the full author list from the article page. |
| `yang2026` | "Yang et al." on transaction classification together with budget prediction | **No matching record found.** The closest topical matches are by other first authors (Fan et al., EMNLP 2025 Industry, arXiv:2601.05271; Yağcı et al., IEEE BigData 2025) | **Unresolved**: supply the source you read, or remove the sentence |
| `liu2008` | Isolation Forest | F. T. Liu, K. M. Ting, Z.-H. Zhou. "Isolation Forest". *Proc. IEEE ICDM 2008*, pp. 413–422 (HW2 ref [2]) | Verified (HW2 reference list) |
| `liu2012` | Isolation-based anomaly detection | F. T. Liu, K. M. Ting, Z.-H. Zhou. "Isolation-Based Anomaly Detection". *ACM Transactions on Knowledge Discovery from Data* 6(1), article 3, pp. 3:1–3:39, 2012. doi:10.1145/2133360.2133363 | Verified (index: DBLP) |
| `breiman2001` | Random Forests | L. Breiman. "Random Forests". *Machine Learning* 45(1), pp. 5–32, 2001 (HW2 ref [5]) | Verified (HW2 reference list) |
| `chen2016` | Scalable boosting | T. Chen, C. Guestrin. "XGBoost: A Scalable Tree Boosting System". *Proc. ACM KDD 2016*, pp. 785–794 (HW2 ref [6]) | Verified (HW2 reference list) |
| `lundberg2017` | SHAP | S. M. Lundberg, S.-I. Lee. "A Unified Approach to Interpreting Model Predictions". *Advances in Neural Information Processing Systems 30 (NIPS 2017)*, pp. 4765–4774 | Verified (index: NeurIPS proceedings metadata) |
| Taylor and Letham 2018 (in text) | Interpretable forecasting | S. J. Taylor, B. Letham. "Forecasting at Scale". *The American Statistician* 72(1), pp. 37–45, 2018 (HW2 ref [4]) | Verified (HW2 reference list) |
| Hyndman and Koehler 2006 (in text) | Forecast accuracy measures, MASE | R. J. Hyndman, A. B. Koehler. "Another look at measures of forecast accuracy". *International Journal of Forecasting* 22(4), pp. 679–688, 2006 (HW2 ref [3]) | Verified (HW2 reference list) |
| `[1]` | Dataset A on Hugging Face | ziadatalabs. *FreeFinancialTransactions50M*. Hugging Face, revision `98cf38f9b2f1a9994930f52a4d490cb2b5777acc`, CC BY-NC 4.0 (HW2 ref [1]) | Verified (dataset card, `data/raw/PROVENANCE.json`) |
| `[9]` | Rolling chronological validation | Not identifiable from HW1: the reference list is missing | **Unresolved**: name the source you meant. Hyndman & Koehler 2006 covers accuracy measures but not rolling origin; the student must choose and verify |

## Datasets and software

| Item | Record | Status |
|---|---|---|
| Dataset B | D. Yuan et al. (Capital One Research, Google, University of Maryland). "PersonaLedger: Generating Realistic Financial Transactions with Persona Conditioned LLMs and Rule Grounded Feedback". arXiv:2601.03149 (v1 6 Jan 2026, v2 20 Jan 2026). Dataset: huggingface.co/datasets/capitalone/PersonaLedger, revision `c90078ae4ac47e582c9263579466a905fa4adfab`, CC BY 4.0 | The dataset card was verified directly through the Hugging Face API (licence, revision, not gated). The arXiv record was verified (index) through search. The paper's full text could not be fetched (arXiv blocked) |
| scikit-learn | F. Pedregosa et al. "Scikit-learn: Machine Learning in Python". *JMLR* 12, pp. 2825–2830, 2011 (HW2 ref [7]) | Verified (HW2 reference list) |

Sources consulted through search (index pages):
* ojs.aaai.org/index.php/AAAI/article/view/4984
* ijeit.misuratau.edu.ly/index.php/ijeit/article/view/609
* dblp.org/rec/bibtex/journals/tkdd/LiuTZ12
* proceedings.neurips.cc (2017, paper 7062)
* arxiv.org/abs/2601.03149
