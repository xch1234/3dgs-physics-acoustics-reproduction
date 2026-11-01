"""Restore the repaired Windows CPU-Torch/Warp environment from its YAML."""
from common import ROOT,AUDIT,run,runtime_env,save
from pathlib import Path
prefix=Path('F:/3dgs-remediation/envs/physgaussian-windows-clean');assert not prefix.exists()
temp=Path('F:/3dgs-remediation/tmpwin');temp.mkdir(exist_ok=True)
env=runtime_env();env.update(TEMP=str(temp),TMP=str(temp),PIP_CACHE_DIR='F:/3dgs-remediation/pip-cache-win',CONDA_PKGS_DIRS='F:/3dgs-remediation/pkgs-win')
run('V03-windows-phys-create',['C:/ProgramData/anaconda3/Scripts/conda.exe','env','create','--yes','--prefix',prefix,'--file',ROOT/'01_PhysGaussian/docs/environment.yml'],env=env)
py=prefix/'python.exe'
run('V03-windows-phys-pip',[py,'-m','pip','check'],env=env)
run('V03-windows-phys-import',[py,'-c','import torch,warp,numpy; from importlib.metadata import version; print(torch.__version__,version("warp-lang"),numpy.__version__)'],env=env)
run('V03-windows-phys-SH',[py,'-u',AUDIT/'sh_cpu_task.py'],env=env)
save('checks/V03-clean-windows-phys.json',dict(passed=True,prefix=str(prefix),scope='Fresh Windows CPU-Torch/Warp YAML installation and CPU SH invariance. Complete CUDA 3DGS rendering uses the separately rebuilt Linux prefix.',repair='Added public CPU wheel index required by pinned torch==2.0.0+cpu; corrected name and removed damaged absolute prefix.'))
