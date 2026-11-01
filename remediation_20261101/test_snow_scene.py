"""Integration check of the usable snow option in the full scene wrapper."""
import sys,json,os
from common import ROOT,AUDIT,run,runtime_env,save
clean='physgaussian-clean' in sys.prefix;tag='snow_ficus_clean_env' if clean else 'snow_ficus_local'
config=json.loads((ROOT/'01_PhysGaussian/code/PhysGaussian/config/ficus_config.json').read_text())
config.update(material='snow',E=20000.,nu=.3,density=1000.,additional_material_params=[],frame_num=25,g=[0,0,-1],move_camera=False)
path=AUDIT/'snow'/f'{tag}_config.json';path.write_text(json.dumps(config,indent=2))
env=runtime_env(sys.prefix);env['TORCH_HOME']='/opt/3dgs-runtime/torch-cache'
run('V19-'+tag,[sys.executable,'-u',AUDIT/'gpu_task.py','scene','--model',ROOT/'01_PhysGaussian/inputs/ficus_whitebg-trained','--config',path,'--tag',tag,'--correct-sh-frame'],env=env)
m=json.loads((AUDIT/'physics/outputs'/tag/'metrics.json').read_text());assert m['all_checks_passed'] and m['rendered_frames']==25 and 'local_snow_extension' in m
assert m['frames'][-1]['max_displacement']>1e-6
save('checks/V19-'+tag+'.json',dict(passed=True,metrics=m,scope='Full CUDA-rendered Ficus geometry with explicitly artificial local snow material; not real plant physics or paper snow benchmark.'))
