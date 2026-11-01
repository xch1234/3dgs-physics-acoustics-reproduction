import sys,subprocess
from pathlib import Path
a=Path(__file__).resolve().parent
cmd=['wsl','-d','Ubuntu1','--','/opt/3dgs-runtime/envs/physgaussian/bin/python','-u','/mnt/f/System/Desktop/3DGS/复现/remediation_20261101/post_gpu.py']
with (a/'logs/post-gpu-launch.log').open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
sys.exit(r.returncode)
