# Hardware Audit

| Host | Source | Spec |
|---|---|---|
| Execution container (all runs) | Measured (`lscpu`, `free`, `df`, psutil) | Ubuntu 24.04.5, 4 vCPU Intel Xeon @ 2.10 GHz, 16.87 GB RAM, about 61 GB free disk, no GPU |
| Student laptop (target) | **User-reported, not measurable here** | HP Pavilion x360 14, i7-1355U, 16 GB DDR4-3200, Iris Xe, no NVIDIA GPU, Windows 64-bit, about 350 GB free |

No CUDA or GPU is needed: every model is a CPU model from scikit-learn or statsmodels.
