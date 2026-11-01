$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.conda\physgaussian\python.exe'
# Warp 0.10.1 NVRTC cannot open headers through a Chinese include directory.
# This junction points to the same project Conda environment; it is not a copy.
$asciiAlias = Join-Path $env:USERPROFILE '.cache\3dgs-physgaussian'
if (-not (Test-Path -LiteralPath $asciiAlias)) {
    New-Item -ItemType Directory -Force (Split-Path -Parent $asciiAlias) | Out-Null
    New-Item -ItemType Junction -Path $asciiAlias -Target (Split-Path -Parent $pythonExe) | Out-Null
}
$aliasItem = Get-Item -LiteralPath $asciiAlias
$expectedTarget = [IO.Path]::GetFullPath((Split-Path -Parent $pythonExe)).TrimEnd('\')
if ($aliasItem.LinkType -ne 'Junction' -or [IO.Path]::GetFullPath([string]$aliasItem.Target[0]).TrimEnd('\') -ne $expectedTarget) {
    throw "The environment alias already points elsewhere: $asciiAlias. Resolve this path before running."
}
$pythonExe = Join-Path $asciiAlias 'python.exe'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONNOUSERSITE = '1'
$ErrorActionPreference = 'Continue'
& $pythonExe -u (Join-Path $PSScriptRoot 'code\run_mpm.py') 2>&1 | Tee-Object (Join-Path $PSScriptRoot 'logs\mpm.log')
if ($LASTEXITCODE -ne 0) { throw 'PhysGaussian official MPM failed. See logs.' }
Copy-Item (Join-Path $PSScriptRoot 'outputs\mpm_gaussians\metrics.json') (Join-Path $PSScriptRoot 'docs\mpm-metrics.json') -ErrorAction Stop
