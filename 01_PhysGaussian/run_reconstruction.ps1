param([int]$Iterations=30000,[string]$Resume='', [switch]$SkipTraining)
$ErrorActionPreference='Continue'
$windowsScript=(Join-Path $PSScriptRoot 'code\run_reconstruction.sh').Replace('\','/')
$linuxScript=(& wsl -d Ubuntu1 -- wslpath -a $windowsScript).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve the WSL entry path.' }
$arguments=@('-d','Ubuntu1','--','bash','--noprofile','--norc',$linuxScript,'--iterations',"$Iterations")
if ($Resume) {
    $resumePath=(& wsl -d Ubuntu1 -- wslpath -a ((Resolve-Path $Resume).Path.Replace('\','/'))).Trim()
    $arguments+=@('--resume',$resumePath)
}
if ($SkipTraining) { $arguments+='--skip-training' }
& wsl @arguments 2>&1 | Tee-Object (Join-Path $PSScriptRoot 'logs\ficus-reconstruction.log')
if ($LASTEXITCODE -ne 0) { throw 'Ficus reconstruction failed; inspect the stage log.' }
