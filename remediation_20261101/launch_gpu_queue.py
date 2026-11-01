import subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parent
cmd=['wsl','-d','Ubuntu1','--','/opt/3dgs-runtime/envs/physgaussian/bin/python','-u','/mnt/f/System/Desktop/3DGS/复现/remediation_20261101/gpu_queue.py']
with (r/'logs/gpu-queue-launch.log').open('wb') as out:p=subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT)
print('EXIT',p.returncode);sys.exit(p.returncode)
