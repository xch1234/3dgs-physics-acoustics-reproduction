from pathlib import Path
import subprocess,json,time
R=Path(__file__).resolve().parents[1];A=R/'remediation_20261101';cmd=[str(R/'.conda/acoustics/python.exe'),str(A/'run_phase_audio.py')];start=time.time()
with (A/'logs/V08-phase-audio.log').open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
(A/'commands/V08.json').write_text(json.dumps({'argv':cmd,'exit':r.returncode,'elapsed_seconds':time.time()-start},indent=2));print('V08',r.returncode)
