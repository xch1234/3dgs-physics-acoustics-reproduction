param([string[]]$Scenes=@('ficus','bread','pillow2sofa','plane','vasedeck','wolf'))
$ErrorActionPreference='Continue'
$windowsScript=(Join-Path $PSScriptRoot 'code\run_scene_suite.sh').Replace('\','/')
$linuxScript=(& wsl -d Ubuntu1 -- wslpath -a $windowsScript).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve the WSL entry path.' }
& wsl -d Ubuntu1 -- bash --noprofile --norc $linuxScript @Scenes 2>&1 | Tee-Object (Join-Path $PSScriptRoot 'logs\official-scene-suite.log')
if ($LASTEXITCODE -ne 0) { throw 'Scene suite reported a failure; inspect its JSON summary and logs.' }
