import sys
from common import ROOT,AUDIT,run,runtime_env,save
def main():
    env=runtime_env();rows=[]
    for name in ('acoustics','physgaussian'):
        python=ROOT/'.conda'/name/'python.exe'
        rows.append(run('windows-'+name+'-pip',[python,'-m','pip','check'],env=env,required=False))
        rows.append(run('windows-'+name+'-versions',[python,'-c','import sys,numpy,scipy; print(sys.version);print(numpy.__version__,scipy.__version__)'],env=env,required=False))
    scripts=[ROOT/'run_all.ps1',ROOT/'run_full.ps1']
    for folder in ('01_PhysGaussian','02_PAT','03_NeuralSound'):scripts.extend((ROOT/folder).glob('*.ps1'))
    for i,p in enumerate(scripts):
        quoted=str(p).replace("'","''")
        cmd="$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile('"+quoted+"',[ref]$t,[ref]$e)|Out-Null;if($e){throw $e};Write-Output 'PARSED'"
        rows.append(run('powershell-syntax-'+str(i),['powershell','-NoProfile','-Command',cmd],env=env,required=False))
    save('environment-windows.json',rows)
if __name__=='__main__':main()
