"""Project structure audit: required directories/files (master prompt section 5) vs. what exists.

A file counts as PRESENT only if it exists and is non-empty (empty placeholders are not counted).
Also tallies traceability statuses from docs/requirements_traceability.md.
Writes reports/verification/project_inventory.json
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIRS = """configs app app/components app/pages app/utils src src/data src/analytics src/rules src/features
src/models src/models/forecasting src/models/anomaly src/experiments src/evaluation src/assistant src/budget
src/utils scripts tests tests/unit tests/integration tests/regression tests/fixtures docs data/raw data/interim
data/processed data/samples data/external artifacts/forecasting artifacts/anomaly artifacts/metadata
reports/data_audit reports/benchmarks reports/experiments reports/evaluation reports/figures reports/screenshots
reports/final_evidence logs/application logs/training logs/preprocessing logs/testing logs/execution
checkpoints/downloads checkpoints/preprocessing checkpoints/experiments checkpoints/training""".split()

FILES = """CLAUDE.md README.md PROJECT_STATUS.md NEXT_ACTION.md DECISIONS.md KNOWN_ISSUES.md EXPERIMENT_REGISTRY.md
CHANGELOG.md requirements.txt requirements-lock.txt pyproject.toml .python-version .gitignore .env.example
setup.bat run.bat test.bat train.bat setup.ps1 run.ps1 test.ps1 train.ps1
configs/app.yaml configs/dataset.yaml configs/preprocessing.yaml configs/financial_rules.yaml configs/forecasting.yaml
configs/anomaly_detection.yaml configs/experiments.yaml configs/resource_limits.yaml configs/logging.yaml
configs/model_registry.yaml
app/__init__.py app/main.py app/components/__init__.py app/components/sidebar.py app/components/metrics.py
app/components/charts.py app/components/tables.py app/components/alerts.py app/components/upload.py
app/pages/overview.py app/pages/transactions.py app/pages/analytics.py app/pages/ai_predictions.py
app/pages/budget.py app/pages/financial_assistant.py app/utils/__init__.py app/utils/formatting.py
app/utils/validation.py app/utils/session.py app/utils/exports.py
src/__init__.py src/data/__init__.py src/data/download.py src/data/ingestion.py src/data/schema.py
src/data/validation.py src/data/preprocessing.py src/data/profiling.py src/data/storage.py
src/analytics/__init__.py src/analytics/aggregation.py src/analytics/financial_metrics.py
src/analytics/monthly_analysis.py src/analytics/category_analysis.py
src/rules/__init__.py src/rules/transaction_mapping.py src/rules/transaction_status.py src/rules/refund_rules.py
src/rules/currency_rules.py
src/features/__init__.py src/features/feature_engineering.py src/features/temporal_features.py
src/features/account_features.py src/features/feature_validation.py
src/models/__init__.py src/models/forecasting/__init__.py src/models/forecasting/baselines.py
src/models/forecasting/ets.py src/models/forecasting/gradient_boosting.py
src/models/forecasting/forecasting_pipeline.py src/models/forecasting/inference.py
src/models/anomaly/__init__.py src/models/anomaly/robust_zscore.py src/models/anomaly/isolation_forest.py
src/models/anomaly/anomaly_pipeline.py src/models/anomaly/anomaly_scoring.py
src/models/anomaly/synthetic_injection.py
src/experiments/__init__.py src/experiments/data_splitting.py src/experiments/forecasting_experiment.py
src/experiments/anomaly_experiment.py src/experiments/experiment_runner.py src/experiments/experiment_tracking.py
src/evaluation/__init__.py src/evaluation/forecasting_metrics.py src/evaluation/anomaly_metrics.py
src/evaluation/comparison.py src/evaluation/visualizations.py src/evaluation/error_analysis.py
src/assistant/__init__.py src/assistant/intent_detection.py src/assistant/query_executor.py
src/assistant/response_generator.py src/budget/__init__.py src/budget/budget_calculator.py
src/budget/budget_alerts.py src/utils/__init__.py src/utils/logging.py src/utils/reproducibility.py
src/utils/resource_monitor.py src/utils/configuration.py
scripts/setup_environment.py scripts/verify_environment.py scripts/download_dataset.py scripts/verify_dataset.py
scripts/run_audit.py scripts/run_preprocessing.py scripts/build_aggregates.py scripts/create_splits.py
scripts/train_forecasting.py scripts/train_anomaly.py scripts/evaluate_models.py scripts/run_all_tests.py
scripts/run_full_pipeline.py scripts/run_application.py scripts/verify_artifacts.py
scripts/generate_final_evidence.py
tests/conftest.py tests/unit/test_ingestion.py tests/unit/test_validation.py tests/unit/test_preprocessing.py
tests/unit/test_financial_rules.py tests/unit/test_aggregation.py tests/unit/test_forecasting.py
tests/unit/test_anomaly.py tests/unit/test_budget.py tests/unit/test_assistant.py
tests/integration/test_full_pipeline.py tests/integration/test_model_loading.py
tests/integration/test_csv_upload.py tests/integration/test_dashboard.py
tests/regression/test_financial_correctness.py tests/regression/test_data_leakage.py
tests/regression/test_reproducibility.py tests/fixtures/sample_transactions.csv
tests/fixtures/expected_financial_results.json
docs/academic_source_analysis.md docs/requirements_traceability.md docs/requirements_conflicts.md
docs/academic_implementation_matrix.md docs/ARCHITECTURE.md docs/architecture_decisions.md
docs/implementation_roadmap.md docs/hardware_audit.md docs/environment_audit.md docs/resource_budget.md
docs/connectors_and_tools_audit.md docs/local_vs_colab_benchmark.md docs/dataset_provenance.md
docs/DATA_DICTIONARY.md docs/data_quality.md docs/DATA_PIPELINE.md docs/FINANCIAL_RULES.md
docs/model_methodology.md docs/experimental_design.md docs/leakage_analysis.md docs/evaluation_methodology.md
docs/KNOWN_LIMITATIONS.md docs/REPRODUCIBILITY.md docs/installation_guide.md docs/USER_GUIDE.md
docs/troubleshooting.md""".split()


def main() -> None:
    dirs = {d: (ROOT / d).is_dir() for d in DIRS}
    files = {}
    for f in FILES:
        p = ROOT / f
        files[f] = "present" if p.is_file() and p.stat().st_size > 0 else ("empty" if p.exists() else "missing")
    extra = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*.py")
                   if ".venv" not in p.parts and str(p.relative_to(ROOT)) not in files)
    tr = (ROOT / "docs/requirements_traceability.md").read_text()
    rows = [ln for ln in tr.splitlines() if ln.startswith("| ") and not ln.startswith("| ID")
            and not set(ln) <= set("|- ")]
    tally: dict[str, int] = {}
    for ln in rows:
        last = ln.rstrip(" |").split("|")[-1].strip()
        key = re.match(r"(PASS|PARTIAL|NOT TESTED|N/A|BLOCKED|FAIL|UNKNOWN)", last)
        k = key.group(1) if key else "UNPARSED"
        tally[k] = tally.get(k, 0) + 1
    out = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
           "dirs_present": sum(dirs.values()), "dirs_required": len(dirs),
           "dirs_missing": [d for d, ok in dirs.items() if not ok],
           "files_present": sum(v == "present" for v in files.values()), "files_required": len(files),
           "files_empty": [f for f, v in files.items() if v == "empty"],
           "files_missing": [f for f, v in files.items() if v == "missing"],
           "extra_python_files_not_in_master_list": extra,
           "traceability_rows": len(rows), "traceability_status_tally": tally}
    (ROOT / "reports/verification/project_inventory.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "files_missing"}, indent=2))
    print("missing files:", len(out["files_missing"]))
    if "--list-missing" in sys.argv:
        print("\n".join(out["files_missing"]))


if __name__ == "__main__":
    main()
