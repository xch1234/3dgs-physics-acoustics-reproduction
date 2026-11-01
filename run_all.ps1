$ErrorActionPreference = 'Stop'
# Baseline only: CPU FEM, CPU acoustics, then two Warp CUDA experiments.
# Full extended experiments have a separate run_full.ps1 entry.
# Existing outputs and latest-run logs are regenerated. No package installation.
foreach ($entry in @('03_NeuralSound\run.ps1', '02_PAT\run.ps1', '01_PhysGaussian\run.ps1', '01_PhysGaussian\run_ficus.ps1')) {
    Write-Host "Running $entry"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot $entry)
    if ($LASTEXITCODE -ne 0) { throw "Experiment failed: $entry" }
}
# Each experiment updates its document snapshots; refresh the file audit last.
$env:PYTHONUTF8 = '1'
$env:PYTHONNOUSERSITE = '1'
& (Join-Path $PSScriptRoot '.conda\acoustics\python.exe') (Join-Path $PSScriptRoot 'verify_artifacts.py')
if ($LASTEXITCODE -ne 0) { throw 'Artifact audit failed.' }
