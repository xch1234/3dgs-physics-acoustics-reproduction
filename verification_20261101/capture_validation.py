"""Capture real child exit status instead of PowerShell's native-stderr wrapper status."""
import sys
from common import ROOT,AUDIT,run,runtime_env
script=sys.argv[1]
path='/mnt/f/System/Desktop/3DGS/'+ROOT.name+'/verification_20261101/'+script
run('captured-'+script.removesuffix('.py'),['wsl.exe','-d','Ubuntu1','--','env','PYTHONDONTWRITEBYTECODE=1','/opt/3dgs-runtime/envs/physgaussian/bin/python','-u',path],env=runtime_env())
