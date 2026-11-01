param([ValidateSet('bem','example','labels','audio','benchmark','example_labels','example_radiation','example_hybrid','predictions')][string]$Task='example',[switch]$Extended)
if ($Extended -and $Task -ne 'example_hybrid') { throw '-Extended applies only to example_hybrid.' }
$ErrorActionPreference='Continue'
$windowsScript=(Join-Path $PSScriptRoot 'code\run_neural_linux.sh').Replace('\','/')
$linuxScript=(& wsl -d Ubuntu1 -- wslpath -a $windowsScript).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve the WSL entry path.' }
$arguments=@('-d','Ubuntu1','--','bash','--noprofile','--norc',$linuxScript,$Task)
if ($Task -eq 'bem') { $arguments+=@('--backend','numba','--precision','double','--tolerance','1e-8') }
if (($Task -eq 'example') -and (Test-Path (Join-Path $PSScriptRoot 'outputs\official_example\voxel.npy'))) { $arguments+='--reuse-voxel' }
if ($Extended) { $arguments+=@('--iterations','10000','--extended') }
$logTag=if ($Extended) { "$Task-extended" } else { $Task }
& wsl @arguments 2>&1 | Tee-Object (Join-Path $PSScriptRoot "logs\$logTag-numerical.log")
if ($LASTEXITCODE -ne 0) { throw "NeuralSound $Task stage failed; inspect the log." }
