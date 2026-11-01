$ErrorActionPreference='Continue'
$windowsScript=(Join-Path $PSScriptRoot 'code\run_reconstructed_simulation.sh').Replace('\','/')
$linuxScript=(& wsl -d Ubuntu1 -- wslpath -a $windowsScript).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve WSL entry path.' }
& wsl -d Ubuntu1 -- bash --noprofile --norc $linuxScript 2>&1 | Tee-Object (Join-Path $PSScriptRoot 'logs\ficus-reconstructed-simulation.log')
if ($LASTEXITCODE -ne 0) { throw 'Simulation using the newly trained Ficus model failed.' }
