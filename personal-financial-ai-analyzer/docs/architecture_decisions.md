# Architecture Decisions

The authoritative log is `../DECISIONS.md` (D-01…D-19). HW1/HW2 conflicts are in `requirements_conflicts.md` (CF-01…CF-16). Summary of the architectural decisions:

* **Hybrid design** (HW1 §1.3.3): deterministic totals, with ML only for forecasting and anomalies.
* **Single rules code path** for the dataset and for uploads.
* **Integer-cents money** (D-15), with currency always part of the key.
* **Memory-guarded child-process partitions** (D-11).
* **Training separated from serving.** The app loads versioned artifacts only (HW2 6.4). A global IF is deployed because a per-account IF cannot be pre-trained for unseen users (D-07).
* **Streamlit `st.navigation`** with six explicit page callables.
* **Small trained artifacts committed** (1.6 MB) so a fresh clone runs (D-19).
