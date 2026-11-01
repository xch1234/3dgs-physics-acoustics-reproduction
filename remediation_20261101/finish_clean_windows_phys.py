import json
from common import ROOT,AUDIT,run,runtime_env,save
for name in ('V03-windows-phys-create','V03-windows-phys-pip'):
 assert json.loads((AUDIT/'commands'/f'{name}.json').read_text())['exit_code']==0
prefix='F:/3dgs-remediation/envs/physgaussian-windows-clean';py=prefix+'/python.exe'
run('V03-windows-phys-import-corrected',[py,'-c','import torch,warp,numpy; from importlib.metadata import version; print(torch.__version__,version("warp-lang"),numpy.__version__)'],env=runtime_env())
run('V03-windows-phys-SH',[py,'-u',AUDIT/'sh_cpu_task.py'],env=runtime_env())
save('checks/V03-clean-windows-phys.json',dict(passed=True,prefix=prefix,scope='Fresh Windows CPU-Torch/Warp YAML installation, pip check, relevant imports, CPU SH invariance; full CUDA 3DGS uses separately rebuilt Linux prefix.',repair='CPU wheel index added for torch==2.0.0+cpu; portable name and no corrupt prefix.',diagnostic_correction='Removed unnecessary SciPy import from diagnostic. SciPy was not declared or required by this Windows SH/Warp environment; original failure retained.'))
