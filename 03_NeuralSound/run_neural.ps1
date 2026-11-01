param([ValidateSet('vibration','radiation')][string]$Task='vibration',[int]$Epochs=0,[switch]$Resume)
if ($Epochs -le 0) { if ($Task -eq 'vibration') { $Epochs=200 } else { $Epochs=100 } }
$ErrorActionPreference='Continue'
$windowsScript=(Join-Path $PSScriptRoot 'code\run_neural_linux.sh').Replace('\','/')
$linuxScript=(& wsl -d Ubuntu1 -- wslpath -a $windowsScript).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve the WSL entry path.' }
$arguments=@('-d','Ubuntu1','--','bash','--noprofile','--norc',$linuxScript,$Task,'--epochs',"$Epochs")
if ($Resume) { $arguments += '--resume' }
& wsl @arguments 2>&1 | Tee-Object (Join-Path $PSScriptRoot "logs\$Task-training.log")
if ($LASTEXITCODE -ne 0) { throw "NeuralSound $Task training failed. Inspect the log." }
