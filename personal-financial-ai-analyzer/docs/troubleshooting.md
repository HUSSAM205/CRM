# Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `py -3.12` not found | Install Python 3.12 (64-bit) and re-run `setup.bat`. |
| PowerShell refuses `.ps1` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use the `.bat` files. |
| "Map these required columns first" | Choose the Date/time, Amount and Currency columns in the mapping boxes. |
| "The file has no status column…" | Tick "All rows in this file are completed" if that is true. |
| Forecast says "Not enough history" | It needs at least 12 months with spending in that currency (HW2 5.4). |
| No anomaly candidates | It needs more than 3 months of data and at least 5 earlier spending records. |
| A pipeline step was killed for memory | The guard stopped a worker above 4 GB, or the system had less than 3 GB free. Close other applications and rerun `train.bat`; completed steps are skipped. Limits are in `configs/resource_limits.yaml`. |
| Download fails behind a proxy or firewall | Rerun `train.bat`; the download resumes. `huggingface.co` and its CDN must be reachable. |
| Changed code is not reflected in the running app | Stop and restart `run.bat`: Streamlit caches imported modules. |
