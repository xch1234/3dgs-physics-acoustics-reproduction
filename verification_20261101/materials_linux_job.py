from common import AUDIT,run,runtime_env
p='/opt/3dgs-runtime/envs/physgaussian'
run('materials-fresh-linux',[p+'/bin/python','-u',str(AUDIT/'materials_linux.py')],env=runtime_env(p))
