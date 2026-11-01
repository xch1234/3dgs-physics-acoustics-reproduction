from common import ROOT,AUDIT,run,runtime_env
py='F:/3dgs-remediation/envs/acoustics-clean/python.exe'
run('V30-gdown-install',[py,'-m','pip','install','gdown==5.2.0'],env=runtime_env())
run('V30-author-model-downloads',[py,'-u',AUDIT/'recheck_model_downloads.py'],env=runtime_env())
