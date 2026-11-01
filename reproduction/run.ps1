param([switch]$SkipOfficial)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.conda\acoustics\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Missing Conda environment. See reproduction/README.md.' }
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:NUMBA_NUM_THREADS = '1'
$env:MPLBACKEND = 'Agg'
$env:PYTHONNOUSERSITE = '1'
# Directly invoking this Conda interpreter also needs its DLL directories on Windows.
$env:PATH = "$(Split-Path -Parent $pythonExe);$(Join-Path (Split-Path -Parent $pythonExe) 'Library\bin');$env:PATH"
$ErrorActionPreference = 'Continue'
& $pythonExe (Join-Path $PSScriptRoot 'traditional\run_experiment.py') 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot 'logs\traditional-run.log')
$runCode = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($runCode -ne 0) { throw 'Traditional experiment failed; see logs.' }
if (-not $SkipOfficial) {
    $ErrorActionPreference = 'Continue'
    & $pythonExe (Join-Path $PSScriptRoot 'neuralsound\run_official_fem.py') 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot 'logs\official-fem-run.log')
    $runCode = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($runCode -ne 0) { throw 'Official FEM experiment failed; see logs.' }
}
