$ErrorActionPreference = 'Stop'
$pythonExe = Join-Path $env:USERPROFILE '.cache\3dgs-physgaussian\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Run 01_PhysGaussian/run.ps1 first to prepare the environment alias.' }
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONNOUSERSITE='1'
$ErrorActionPreference = 'Continue'
& $pythonExe -u (Join-Path $PSScriptRoot 'code\run_ficus.py') 2>&1 | Tee-Object (Join-Path $PSScriptRoot 'logs\ficus.log')
if ($LASTEXITCODE -ne 0) { throw 'Ficus short simulation failed. See logs.' }
Copy-Item (Join-Path $PSScriptRoot 'outputs\ficus_short\metrics.json') (Join-Path $PSScriptRoot 'docs\ficus-metrics.json') -ErrorAction Stop
