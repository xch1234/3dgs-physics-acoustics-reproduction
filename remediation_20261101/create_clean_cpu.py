from pathlib import Path
import subprocess,json,time,os
R=Path(__file__).resolve().parents[1];A=R/'remediation_20261101';prefix=Path('F:/3dgs-remediation/envs/acoustics-clean');assert not prefix.exists(),'Fresh environment prefix must not exist'
cmd=['C:/ProgramData/anaconda3/Scripts/conda.exe','env','create','--yes','--prefix',str(prefix),'--file',str(R/'02_PAT/docs/environment.yml')];start=time.time()
with (A/'logs/V30-conda-clean-create.log').open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
row={'argv':cmd,'exit':r.returncode,'seconds':time.time()-start,'prefix':str(prefix)}
(A/'commands/V30-create.json').write_text(json.dumps(row,indent=2));print('CREATE',r.returncode,flush=True)
if r.returncode:raise SystemExit(r.returncode)
for name,args in [('pip-check',['-m','pip','check']),('imports',['-c','import numpy,scipy,numba,matplotlib,mcubes; print(numpy.__version__,scipy.__version__,numba.__version__)']),('PAT-fresh',['-u',str(A/'run_phase_audio.py')])]:
 command=[str(prefix/'python.exe'),*args];start=time.time()
 with (A/'logs'/f'V30-{name}.log').open('wb') as f:r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
 (A/'commands'/f'V30-{name}.json').write_text(json.dumps({'argv':command,'exit':r.returncode,'seconds':time.time()-start},indent=2));print(name,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
(A/'checks/V30-clean-cpu.json').write_text(json.dumps({'passed':True,'prefix':str(prefix),'scope':'fresh Windows Conda acoustics environment created from repaired YAML; imports, pip check and complete local PAT+phase chain executed; not a new physical machine or complete Linux GPU rebuild'},indent=2))
