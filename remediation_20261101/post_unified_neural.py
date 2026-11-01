import time
from common import ROOT,AUDIT,run,runtime_env,save
while not (AUDIT/'post-gpu-complete.json').exists():time.sleep(10)
prefix='/opt/3dgs-runtime/envs/physgaussian';row=run('V31-unified-neural-box',[prefix+'/bin/python','-u',AUDIT/'unified_neural_box.py'],env=runtime_env(prefix),required=False)
save('unified-neural-complete.json',row)
