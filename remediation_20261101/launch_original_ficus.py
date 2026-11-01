from common import ROOT,AUDIT,run,runtime_env
run('V30-canonical-ficus',['F:/3dgs-remediation/envs/acoustics-clean/python.exe','-u',AUDIT/'check_original_ficus.py'],env=runtime_env(),timeout=3600)
