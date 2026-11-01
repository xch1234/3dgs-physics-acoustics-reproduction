$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.conda\acoustics\python.exe'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONNOUSERSITE = '1'
$env:PATH = "$(Split-Path -Parent $pythonExe)\Library\bin;$env:PATH"
$ErrorActionPreference = 'Continue'
& $pythonExe -u (Join-Path $PSScriptRoot 'code\run_pat.py') 2>&1 | Tee-Object (Join-Path $PSScriptRoot 'logs\pat.log')
if ($LASTEXITCODE -ne 0) { throw 'PAT experiment failed. See logs.' }
Copy-Item (Join-Path $PSScriptRoot 'outputs\pat_pipeline\metrics.json') (Join-Path $PSScriptRoot 'docs\metrics.json') -ErrorAction Stop
