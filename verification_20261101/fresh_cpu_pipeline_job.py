import time
from common import AUDIT,run,runtime_env
while not (AUDIT/'commands/fresh-bem-labels.json').exists():time.sleep(5)
prefix='/opt/3dgs-runtime/envs/neuralsound'
run('fresh-fem-pat-chain',[prefix+'/bin/python','-u',str(AUDIT/'fresh_cpu_pipeline.py')],env=runtime_env(prefix))
