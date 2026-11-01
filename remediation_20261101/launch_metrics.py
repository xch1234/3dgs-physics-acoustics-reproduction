import subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parent
cmd=['wsl','-d','Ubuntu1','--','/opt/3dgs-runtime/envs/physgaussian/bin/python','-u','/mnt/f/System/Desktop/3DGS/复现/remediation_20261101/run_native_metrics.py']
with (r/'logs/native-launch.log').open('wb') as out:p=subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT)
print('EXIT',p.returncode);sys.exit(p.returncode)
