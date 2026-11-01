"""Remaining full anisotropy control after the other GPU jobs finish."""
import os,sys,time,json
from common import ROOT,AUDIT,run,runtime_env,save
while not (AUDIT/'gpu-queue-complete.json').exists():time.sleep(10)
prefix='/opt/3dgs-runtime/envs/physgaussian';py=prefix+'/bin/python';env=runtime_env(prefix)
env['TORCH_HOME']='/opt/3dgs-runtime/torch-cache';env['PHYSGAUSSIAN_SOURCE']='/opt/3dgs-runtime/PhysGaussian-source'
env['GIT_CONFIG_COUNT']='1';env['GIT_CONFIG_KEY_0']='core.autocrlf';env['GIT_CONFIG_VALUE_0']='true'
repo=ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting';source=ROOT/'01_PhysGaussian/inputs/nerf_synthetic_ficus'
out=AUDIT/'physics/outputs/ficus_anisotropy';rows=[]
def job(name,script,args,cwd=None):
 row=run(name,[py,'-u',script,*map(str,args)],cwd=cwd,env=env,required=False);rows.append(row);save('gpu-followup-state.json',rows);return row['exit_code']==0
ok=job('V28-aniso-train',AUDIT/'aniso_task.py',['--aniso-threshold',5,'--aniso-weight',.01,'-s',source,'-m',out,'--eval','--white_background','--data_device','cpu','--resolution',1,'--iterations',30000,'--port',6041,'--test_iterations',30000,'--save_iterations',7000,15000,30000,'--checkpoint_iterations',30000],repo)
if ok:
 ok=job('V28-aniso-render',repo/'render.py',['-s',source,'-m',out,'--eval','--white_background','--data_device','cpu','--resolution',1,'--iteration',30000,'--skip_train'],repo)
if ok:ok=job('V28-aniso-evaluate',AUDIT/'eval_task.py',['--model',out,'--tag','anisotropy_30000'])
if ok:ok=job('V28-aniso-simulation',AUDIT/'gpu_task.py',['scene','--model',out,'--config',ROOT/'01_PhysGaussian/code/PhysGaussian/config/ficus_config.json','--tag','ficus_anisotropy_rerun'])
save('gpu-followup-complete.json',dict(passed=ok,jobs=rows))
