import time
from common import ROOT,AUDIT,run,runtime_env,save
while not (AUDIT/'gpu-final-complete.json').exists():time.sleep(10)
prefix='/opt/3dgs-runtime/envs/neuralsound';env=runtime_env(prefix);env['TORCH_HOME']='/opt/3dgs-runtime/torch-cache'
r=run('V26-independent-new-inference',[prefix+'/bin/python','-u',AUDIT/'check_new_radiation.py'],env=env,required=False)
save('post-gpu-complete.json',r)
