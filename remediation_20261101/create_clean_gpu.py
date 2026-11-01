"""Install a fresh Conda prefix, then rebuild copied CUDA extension sources."""
import os,sys,json,shutil
from pathlib import Path
from common import ROOT,AUDIT,run,runtime_env,save
prefix='/opt/3dgs-remediation/envs/physgaussian-clean'
assert not Path(prefix).exists(), 'Refuse to reuse an environment as a fresh install'
env=runtime_env();env.update(CONDA_PKGS_DIRS='/opt/3dgs-runtime/pkgs',PIP_CACHE_DIR='/opt/3dgs-runtime/pip-cache',TMPDIR='/opt/3dgs-remediation/tmp')
Path(env['TMPDIR']).mkdir(parents=True,exist_ok=True)
run('V30-clean-gpu-conda',['/opt/3dgs-runtime/miniconda3/bin/conda','create','--yes','--prefix',prefix,'--file',ROOT/'01_PhysGaussian/docs/conda-explicit-linux64.txt'],env=env)
python=prefix+'/bin/python'
run('V30-clean-gpu-torch',[python,'-m','pip','install','torch==2.0.0+cu118','torchvision==0.15.1+cu118','--index-url','https://download.pytorch.org/whl/cu118'],env=env)
req=[]
for s in (ROOT/'01_PhysGaussian/docs/requirements-linux-lock.txt').read_text().splitlines():
 if '==' in s and not s.startswith(('torch==','torchvision==')):req.append(s)
req += ['setuptools==69.5.1','wheel']
lock=AUDIT/'clean-gpu-pip.txt';lock.write_text('\n'.join(req)+'\n')
run('V30-clean-gpu-pip',[python,'-m','pip','install','--no-deps','-r',lock],env=env)
env.update(CUDA_HOME=prefix,PATH=prefix+'/bin:'+env['PATH'],LD_LIBRARY_PATH='/usr/lib/wsl/lib:'+prefix+'/lib',MAX_JOBS='1',TORCH_CUDA_ARCH_LIST='8.6')
for name in ('diff-gaussian-rasterization','simple-knn'):
 source=ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting/submodules'/name
 dest=Path('/opt/3dgs-remediation/build')/name
 shutil.copytree(source,dest,ignore=shutil.ignore_patterns('build','*.so','*.egg-info','__pycache__','.git'))
 run('V30-build-'+name,[python,'-m','pip','install','--no-build-isolation','--no-deps',dest],env=env)
run('V30-clean-gpu-pip-check',[python,'-m','pip','check'],env=env)
run('V30-clean-gpu-imports',[python,'-c','import torch,warp,diff_gaussian_rasterization,simple_knn._C; from importlib.metadata import version; print(torch.__version__,version("warp-lang"))'],env=env)
save('checks/V30-clean-gpu-install.json',dict(passed=True,prefix=prefix,scope='Fresh prefix with pinned Conda packages, cached downloads allowed, both CUDA extensions rebuilt; GPU execution will be checked separately. Same machine/driver, not a new-machine experiment.'))
