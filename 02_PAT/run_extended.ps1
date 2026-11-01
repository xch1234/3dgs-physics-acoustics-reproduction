$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$env:PYTHONUTF8='1'
$env:PYTHONNOUSERSITE='1'
$env:PATH="$(Join-Path $root '.conda\acoustics\Library\bin');$env:PATH"
$ErrorActionPreference='Continue'
& (Join-Path $root '.conda\acoustics\python.exe') -u (Join-Path $PSScriptRoot 'code\run_pat_extended.py') 2>&1 | Tee-Object (Join-Path $PSScriptRoot 'logs\pat-extended.log')
if ($LASTEXITCODE -ne 0) { throw 'PAT extended experiment failed; see saved metrics/log.' }
