from common import ROOT,AUDIT,run,runtime_env
run('V08-phase-extensions',[ROOT/'.conda/acoustics/python.exe','-u',AUDIT/'phase_extensions.py'],env=runtime_env())
