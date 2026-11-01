"""Fresh NeuralSound Conda prefix; rebuild sparse convolution from source."""
import os,sys,time,shutil
from pathlib import Path
from common import ROOT,AUDIT,run,runtime_env,save
start=time.monotonic()
while not (AUDIT/'checks/V30-clean-gpu-install.json').exists():
 if time.monotonic()-start>3600:raise RuntimeError('PhysGaussian build has not passed; do not start another heavy build')
 time.sleep(10)
prefix='/opt/3dgs-remediation/envs/neuralsound-clean';assert not Path(prefix).exists()
env=runtime_env();env.update(CONDA_PKGS_DIRS='/opt/3dgs-runtime/pkgs',PIP_CACHE_DIR='/opt/3dgs-runtime/pip-cache',TMPDIR='/opt/3dgs-remediation/tmp')
run('V30-neural-conda',['/opt/3dgs-runtime/miniconda3/bin/conda','create','--yes','--prefix',prefix,'--file',ROOT/'03_NeuralSound/docs/conda-explicit-linux64.txt'],env=env)
py=prefix+'/bin/python';env.update(CUDA_HOME=prefix,PATH=prefix+'/bin:'+env['PATH'],LD_LIBRARY_PATH='/usr/lib/wsl/lib:'+prefix+'/lib',LIBRARY_PATH='/usr/lib/wsl/lib:'+prefix+'/lib',MAX_JOBS='1',TORCH_CUDA_ARCH_LIST='8.6')
run('V30-neural-torch',[py,'-m','pip','install','torch==2.0.0+cu118','torchvision==0.15.1+cu118','--index-url','https://download.pytorch.org/whl/cu118'],env=env)
req=[s for s in (ROOT/'03_NeuralSound/docs/requirements-linux-lock.txt').read_text().splitlines() if '==' in s and not s.startswith(('MinkowskiEngine==','torch==','torchvision==','torch-scatter=='))]
req+=['setuptools==69.5.1','wheel'];lock=AUDIT/'clean-neural-pip.txt';lock.write_text('\n'.join(req)+'\n')
run('V30-neural-pip',[py,'-m','pip','install','--no-deps','-r',lock],env=env)
run('V30-neural-scatter',[py,'-m','pip','install','--no-deps','torch-scatter==2.1.2+pt20cu118','--only-binary=:all:','-f','https://data.pyg.org/whl/torch-2.0.0+cu118.html'],env=env)
dest=Path('/opt/3dgs-remediation/build/MinkowskiEngine')
shutil.copytree(ROOT/'03_NeuralSound/code/MinkowskiEngine',dest,ignore=shutil.ignore_patterns('build','*.so','*.egg-info','__pycache__','.git'))
run('V30-neural-Minkowski-build',[py,'setup.py','install','--force_cuda','--blas=openblas','--blas_include_dirs='+prefix+'/include','--blas_library_dirs='+prefix+'/lib'],cwd=dest,env=env)
run('V30-neural-pip-check',[py,'-m','pip','check'],env=env)
run('V30-neural-imports',[py,'-c','import torch,torch_scatter,MinkowskiEngine,bempp.api,pycuda,pyopencl; print(torch.__version__,MinkowskiEngine.__version__,pyopencl.get_platforms())'],env=env)
save('checks/V30-clean-neural-install.json',dict(passed=True,prefix=prefix,scope='Fresh Conda explicit package installation, pinned pip packages, rebuilt MinkowskiEngine; GPU inference tested separately; same physical machine.'))
