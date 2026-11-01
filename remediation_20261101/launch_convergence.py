import subprocess,time,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/'remediation_20261101';cmd=[str(R/'.conda/acoustics/python.exe'),str(A/'test_convergence.py')];start=time.time()
with (A/'logs/V09-convergence.log').open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
(A/'commands/V09-convergence.json').write_text(json.dumps({'argv':cmd,'exit':r.returncode,'seconds':time.time()-start},indent=2));print('EXIT',r.returncode)
