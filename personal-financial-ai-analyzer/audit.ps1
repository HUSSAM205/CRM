# Read-only verification: dataset identity, manifest, full reconciliation, artifact reload, tests.
# Requires data\raw\transactions_50M.parquet (run .\train.ps1 or scripts\download_dataset.py first).
$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"
foreach ($s in @("scripts\verify_dataset.py", "scripts\audit\dataset_manifest.py", "scripts\audit\reconcile_granular.py",
                 "scripts\verify_artifacts.py", "scripts\run_all_tests.py")) {
    & $py $s
    if ($LASTEXITCODE -ne 0) { Write-Error "audit step failed: $s"; exit 1 }
}
