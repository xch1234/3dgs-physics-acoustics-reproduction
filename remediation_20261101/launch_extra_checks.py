import sys
from common import ROOT,AUDIT,run
if sys.argv[1]=='dependencies':
 run('V30-dependency-sources',[sys.executable,'-u',AUDIT/'check_dependency_sources.py'])
else:
 run('V30-clean-pat-queue',['wsl','-d','Ubuntu1','--','/opt/3dgs-runtime/envs/physgaussian/bin/python','-u','/mnt/f/System/Desktop/3DGS/复现/remediation_20261101/clean_pat_task.py'])
