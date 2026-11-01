$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.conda\acoustics\python.exe'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONNOUSERSITE = '1'
$env:PATH = "$(Split-Path -Parent $pythonExe)\Library\bin;$env:PATH"
$ErrorActionPreference = 'Continue'
& $pythonExe -u (Join-Path $PSScriptRoot 'code\run_official_fem.py') 2>&1 | Tee-Object (Join-Path $PSScriptRoot 'logs\official-fem.log')
if ($LASTEXITCODE -ne 0) { throw 'Official FEM failed. See logs.' }
Copy-Item (Join-Path $PSScriptRoot 'outputs\official_fem\metrics.json') (Join-Path $PSScriptRoot 'docs\metrics.json') -ErrorAction Stop
Copy-Item (Join-Path $PSScriptRoot 'outputs\official_fem\RESULTS.zh-CN.md') (Join-Path $PSScriptRoot 'docs\RESULTS.md') -ErrorAction Stop
