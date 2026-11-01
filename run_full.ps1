param([switch]$ResumeTraining)
# Requires the documented Conda environments and preserved input datasets.
# Sequential GPU execution; regenerates stage outputs and final reports.
$ErrorActionPreference='Stop'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:MPLCONFIGDIR=Join-Path $PSScriptRoot 'reproduction\cache\matplotlib'
function Invoke-Entry([string]$Relative, [string[]]$Arguments=@()) {
    $ErrorActionPreference='Continue'
    Write-Host "Running $Relative $Arguments"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot $Relative) @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Failed: $Relative" }
}
function Invoke-LinuxScript([string]$Relative) {
    $windowsScript=(Join-Path $PSScriptRoot $Relative).Replace('\','/')
    $ErrorActionPreference='Continue'
    $linuxScript=(& wsl -d Ubuntu1 -- wslpath -a $windowsScript).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve WSL path.' }
    & wsl -d Ubuntu1 -- bash --noprofile --norc $linuxScript
    if ($LASTEXITCODE -ne 0) { throw "Failed: $Relative" }
}
Invoke-Entry 'run_all.ps1'
Invoke-Entry '02_PAT\run_extended.ps1'
Invoke-Entry '02_PAT\run_additional.ps1' @('-Task','moving')
Invoke-Entry '02_PAT\run_additional.ps1' @('-Task','basis')
Invoke-Entry '02_PAT\run_fem.ps1'
Invoke-Entry '01_PhysGaussian\run_scenes.ps1'
Invoke-Entry '03_NeuralSound\run_numerical.ps1' @('-Task','example')
Invoke-Entry '03_NeuralSound\run_numerical.ps1' @('-Task','labels')
foreach ($taskName in @('vibration','radiation')) {
    $entryArgs=@('-Task',$taskName)
    if ($ResumeTraining) { $entryArgs+='-Resume' }
    Invoke-Entry '03_NeuralSound\run_neural.ps1' $entryArgs
}
Invoke-Entry '03_NeuralSound\run_numerical.ps1' @('-Task','audio')
Invoke-Entry '03_NeuralSound\run_numerical.ps1' @('-Task','predictions')
Invoke-Entry '03_NeuralSound\run_numerical.ps1' @('-Task','benchmark')
Invoke-Entry '03_NeuralSound\run_numerical.ps1' @('-Task','example_hybrid')
Invoke-Entry '03_NeuralSound\run_numerical.ps1' @('-Task','example_hybrid','-Extended')
Invoke-Entry '03_NeuralSound\run_numerical.ps1' @('-Task','example_labels')
Invoke-Entry '03_NeuralSound\run_numerical.ps1' @('-Task','example_radiation')
Invoke-Entry '01_PhysGaussian\run_reconstruction.ps1'
Invoke-Entry '01_PhysGaussian\run_reconstructed_simulation.ps1'
Invoke-LinuxScript 'reproduction\run_scope_extensions.sh'
Invoke-LinuxScript 'reproduction\export_linux_environments.sh'
$windowsSummary=(Join-Path $PSScriptRoot '01_PhysGaussian\code\summarize_official_scenes.py').Replace('\','/')
$ErrorActionPreference='Continue'
$linuxSummary=(& wsl -d Ubuntu1 -- wslpath -a $windowsSummary).Trim()
& wsl -d Ubuntu1 -- /opt/3dgs-runtime/envs/physgaussian/bin/python $linuxSummary
if ($LASTEXITCODE -ne 0) { throw 'Scene artifact verification failed.' }
foreach ($checkScript in @('reproduction\check_training_checkpoints.py','reproduction\audit_vibration_arrays.py','03_NeuralSound\code\verify_acoustic_features.py')) {
    $windowsChecks=(Join-Path $PSScriptRoot $checkScript).Replace('\','/')
    $linuxChecks=(& wsl -d Ubuntu1 -- wslpath -a $windowsChecks).Trim()
    & wsl -d Ubuntu1 -- env LD_LIBRARY_PATH=/usr/lib/wsl/lib:/opt/3dgs-runtime/envs/neuralsound/lib OMP_NUM_THREADS=2 /opt/3dgs-runtime/envs/neuralsound/bin/python $linuxChecks
    if ($LASTEXITCODE -ne 0) { throw "Verification failed: $checkScript" }
}
$env:PYTHONUTF8='1'
$env:PYTHONNOUSERSITE='1'
foreach ($script in @('reproduction\audit_traditional.py','reproduction\write_final_reports.py','reproduction\verify_extended_artifacts.py','reproduction\write_acceptance_report.py','reproduction\update_status.py','verify_artifacts.py')) {
    & (Join-Path $PSScriptRoot '.conda\acoustics\python.exe') (Join-Path $PSScriptRoot $script)
    if ($LASTEXITCODE -ne 0) { throw "Failed: $script" }
}
