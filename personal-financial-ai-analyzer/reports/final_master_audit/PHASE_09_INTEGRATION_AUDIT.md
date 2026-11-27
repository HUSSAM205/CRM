# Phase 9: Integration Audit

Status: **COMPLETE**.

| Flow | Evidence |
|---|---|
| CSV upload → validation → rules → aggregation → analytics → predictions → Advisor → Assistant | `test_full_pipeline.py`; browser tasks 1–25 in one session sequence |
| Shared account and currency context | sidebar keys used by every page; assistant scope copy; browser 13 (switch account), 24 (context shown) |
| Saved models only (no retraining in the app) | `test_model_loading.py`; `verify_artifacts.py` 8/8 (with and without datasets) |
| Product forecast = assistant forecast | `forecast_for` → `forecast_product` in both; AppTest and browser 23–24 |
| Deletion propagates (data, budgets, goals, facts, history) | browser 22; settings tests |
