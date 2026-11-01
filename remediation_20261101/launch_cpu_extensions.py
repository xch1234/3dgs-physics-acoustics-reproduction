import sys
from common import ROOT,AUDIT,run,runtime_env
run('V28-pat-extensions',[ROOT/'.conda/acoustics/python.exe','-u',AUDIT/'cpu_extensions.py'],env=runtime_env())
