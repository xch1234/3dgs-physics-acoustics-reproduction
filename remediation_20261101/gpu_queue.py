import os,sys,time,json
from pathlib import Path
from common import ROOT,AUDIT,run,runtime_env,save
# Wait only for our own metrics wrapper to record completion; do not touch other processes.
while not (AUDIT/'checks/V12.json').exists():time.sleep(10)
phys='/opt/3dgs-runtime/envs/physgaussian';neural='/opt/3dgs-runtime/envs/neuralsound';rows=[]
def job(name,prefix,script,args=()):
 env=runtime_env(prefix);env['TORCH_HOME']='/opt/3dgs-runtime/torch-cache';env['PYTHONPATH']=str(ROOT/'01_PhysGaussian/code')+':'+str(ROOT/'03_NeuralSound/code');env['GIT_CONFIG_COUNT']='1';env['GIT_CONFIG_KEY_0']='core.autocrlf';env['GIT_CONFIG_VALUE_0']='true'
 row=run(name,[prefix+'/bin/python','-u',str(script),*map(str,args)],env=env,required=False);rows.append(row);save('gpu-queue-state.json',rows)
job('V17-sh-invariance',phys,AUDIT/'gpu_task.py',['sh'])
job('V19-local-snow',phys,AUDIT/'test_snow.py')
for paper in (False,True):
 tag='paper_schedule' if paper else 'released_profile'
 job('V28-vibration-'+tag,neural,AUDIT/'gpu_task.py',['vibration']+(['--paper-schedule'] if paper else []))
 job('V28-radiation-'+tag,neural,ROOT/'03_NeuralSound/code/train_radiation.py',(['--paper-schedule'] if paper else [])+['--optimizer','cpu_adam','--output-dir',AUDIT/'neural/outputs'/('radiation_'+tag),'--checkpoint-dir','/opt/3dgs-runtime/remediation-checkpoints/'+tag])
# Predeclared local improvement trial. Model selection uses validation loss only;
# no claim of paper accuracy and no tuning based on final test maps.
job('V26-radiation-longer',neural,ROOT/'03_NeuralSound/code/train_radiation.py',['--epochs','400','--batch-size','16','--optimizer','cpu_adam','--no-augmentation','--learning-rate','0.0001','--decay-period','100','--decay-factor','0.5','--output-dir',AUDIT/'neural/outputs/radiation_longer','--checkpoint-dir','/opt/3dgs-runtime/remediation-checkpoints/longer'])
from importlib.util import spec_from_file_location,module_from_spec
spec=spec_from_file_location('scene_catalog',ROOT/'01_PhysGaussian/code/run_scene_suite.py');module=module_from_spec(spec);spec.loader.exec_module(module)
for name,(config,model) in module.SCENES.items():
 job('V28-scene-'+name,phys,AUDIT/'gpu_task.py',['scene','--model',ROOT/'01_PhysGaussian/inputs'/model,'--config',ROOT/'01_PhysGaussian/code/PhysGaussian/config'/config,'--tag',name+'_rerun'])
for name,config,model in [('bread','tear_bread_config.json','bread-trained'),('plane','plane_config.json','plane-trained'),('vasedeck','vasedeck_config.json','vasedeck_whitebg-trained')]:
 job('V17-corrected-'+name,phys,AUDIT/'gpu_task.py',['scene','--model',ROOT/'01_PhysGaussian/inputs'/model,'--config',ROOT/'01_PhysGaussian/code/PhysGaussian/config'/config,'--tag',name+'_corrected_rerun','--correct-sh-frame'])
job('V28-reconstructed-scene',phys,AUDIT/'gpu_task.py',['scene','--model',ROOT/'01_PhysGaussian/outputs/ficus_reconstruction','--config',ROOT/'01_PhysGaussian/code/PhysGaussian/config/ficus_config.json','--tag','ficus_reconstructed_rerun'])
save('gpu-queue-complete.json',{'jobs':len(rows),'failures':[r['name'] for r in rows if r['exit_code']!=0]});print('GPU QUEUE FINISHED',flush=True)
