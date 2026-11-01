from common import AUDIT,run,runtime_env
prefix='/opt/3dgs-runtime/envs/neuralsound'
run('fresh-fem-pat-chain-retry',[prefix+'/bin/python','-u',str(AUDIT/'fresh_cpu_pipeline.py')],env=runtime_env(prefix))
