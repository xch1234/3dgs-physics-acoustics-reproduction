param([string]$Tag='ficus_official_full')
$ErrorActionPreference='Continue'
$windowsScript=(Join-Path $PSScriptRoot 'code\run_official_linux.sh').Replace('\','/')
$linuxScript=(& wsl -d Ubuntu1 -- wslpath -a $windowsScript).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve the WSL entry path.' }
& wsl -d Ubuntu1 -- bash --noprofile --norc $linuxScript --tag $Tag 2>&1 | Tee-Object (Join-Path $PSScriptRoot "logs\$Tag.log")
if ($LASTEXITCODE -ne 0) { throw 'Official PhysGaussian Linux pipeline failed.' }
