param([ValidateSet('moving','basis')][string]$Task='moving')
$ErrorActionPreference='Continue'
$root=Split-Path -Parent $PSScriptRoot
$env:PYTHONUTF8='1'
$env:PYTHONNOUSERSITE='1'
$env:PATH="$(Join-Path $root '.conda\acoustics\Library\bin');$env:PATH"
if ($Task -eq 'basis') {
    $windowsScript=(Join-Path $PSScriptRoot 'code\run_modalsound_basis.sh').Replace('\','/')
    $linuxScript=(& wsl -d Ubuntu1 -- wslpath -a $windowsScript).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve WSL script path.' }
    & wsl -d Ubuntu1 -- bash --noprofile --norc $linuxScript
    if ($LASTEXITCODE -ne 0) { throw 'ModalSound C++ basis build/run failed.' }
    $script='check_modalsound_basis.py'
} else {
    $script='run_moving_listener.py'
}
& (Join-Path $root '.conda\acoustics\python.exe') -u (Join-Path $PSScriptRoot "code\$script") 2>&1 | Tee-Object (Join-Path $PSScriptRoot "logs\$Task-additional.log")
if ($LASTEXITCODE -ne 0) { throw "PAT $Task experiment failed." }
