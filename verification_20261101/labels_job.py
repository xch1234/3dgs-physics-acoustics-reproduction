from common import AUDIT,run,runtime_env
prefix='/opt/3dgs-runtime/envs/neuralsound'
run('fresh-bem-labels',[prefix+'/bin/python','-u',str(AUDIT/'labels_isolated.py')],env=runtime_env(prefix))
