# Local vs Colab

**Decision: Colab not needed.**

Every step completed within the 4 GB per-worker budget. Full-data scans run at 23–69M rows/s, and the slowest step (the forecasting experiment) took 529 s on 4 vCPU. No measured limitation justifies moving work to Colab, which also offers no GPU benefit for these CPU models. Evidence: `reports/verification/resource_benchmark_report.md`.
