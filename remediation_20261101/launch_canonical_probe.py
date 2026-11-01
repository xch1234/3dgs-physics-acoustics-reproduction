from common import ROOT,AUDIT,run,runtime_env
run('V30-canonical-access',['F:/3dgs-remediation/envs/physgaussian-windows-clean/python.exe','-u',AUDIT/'probe_canonical_source.py'],env=runtime_env(),timeout=600)
