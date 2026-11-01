"""Last serial GPU jobs, including fresh-prefix execution and shared-object demo."""
import time,json
from common import ROOT,AUDIT,run,runtime_env,save
while not (AUDIT/'gpu-followup-complete.json').exists():time.sleep(10)
phys='/opt/3dgs-runtime/envs/physgaussian';neural='/opt/3dgs-runtime/envs/neuralsound';clean='/opt/3dgs-remediation/envs/physgaussian-clean';rows=[]
def job(name,prefix,script,args=(),cwd=None):
 env=runtime_env(prefix);env['TORCH_HOME']='/opt/3dgs-runtime/torch-cache';env['TMPDIR']='/opt/3dgs-runtime/tmp';env['GIT_CONFIG_COUNT']='1';env['GIT_CONFIG_KEY_0']='core.autocrlf';env['GIT_CONFIG_VALUE_0']='true'
 row=run(name,[prefix+'/bin/python','-u',script,*map(str,args)],cwd=cwd,env=env,required=False);rows.append(row);save('gpu-final-state.json',rows);return row['exit_code']==0
job('V28-neural-example',neural,AUDIT/'neural_extension_task.py',['example'])
job('V28-neural-hybrid',neural,AUDIT/'neural_extension_task.py',['hybrid'])
job('V28-neural-hybrid-extended',neural,AUDIT/'neural_extension_task.py',['hybrid','--extended','--iterations','10000'])
job('V28-neural-example-acoustics',neural,AUDIT/'neural_extension_task.py',['acoustics'])
job('V28-neural-audio',neural,AUDIT/'neural_extension_task.py',['audio'])
job('V31-shared-beam',phys,AUDIT/'unified_beam.py')
if (AUDIT/'checks/V30-clean-gpu-install.json').exists():
 repo=ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting';source=ROOT/'01_PhysGaussian/inputs/nerf_synthetic_ficus';out=AUDIT/'physics/outputs/clean_env_300'
 ok=job('V30-clean-train',clean,repo/'train.py',['-s',source,'-m',out,'--eval','--white_background','--data_device','cpu','--resolution',1,'--iterations',300,'--port',6042,'--test_iterations',300,'--save_iterations',300],repo)
 if ok:ok=job('V30-clean-render',clean,repo/'render.py',['-s',source,'-m',out,'--eval','--white_background','--data_device','cpu','--resolution',1,'--iteration',300,'--skip_train'],repo)
 if ok:ok=job('V30-clean-evaluate',clean,AUDIT/'clean_eval_task.py',['--output-dir',out,'--iteration',300])
 if ok:ok=job('V30-clean-warp-snow',clean,AUDIT/'test_snow.py')
 save('checks/V30-clean-gpu-execution.json',dict(passed=ok,scope='Fresh-prefix 300-step 3DGS training + 200-view render/evaluation and local Warp snow tests. Environment smoke test, not 30k reconstruction quality or another physical machine.'))
else:save('checks/V30-clean-gpu-execution.json',dict(passed=False,reason='Fresh-prefix installation did not pass.'))
if (AUDIT/'checks/V30-clean-neural-install.json').exists():
 clean_neural='/opt/3dgs-remediation/envs/neuralsound-clean'
 ok=job('V30-clean-neural-voxel-scatter',clean_neural,AUDIT/'clean_neural_smoke.py')
 if ok:ok=job('V30-clean-neural-inference',clean_neural,AUDIT/'check_new_radiation.py',['--namespace','neural_clean','--profiles','radiation_released_profile'])
 save('checks/V30-clean-neural-execution.json',dict(passed=ok,scope='Actual CUDA voxelizer, scatter, and complete 24-map AcousticNet inference in fresh prefix. Fixed current trained weights; not fresh retraining or another machine.'))
else:save('checks/V30-clean-neural-execution.json',dict(passed=False,reason='Fresh NeuralSound prefix installation did not pass.'))
save('gpu-final-complete.json',dict(jobs=len(rows),failed=[r['name'] for r in rows if r['exit_code']!=0]))
