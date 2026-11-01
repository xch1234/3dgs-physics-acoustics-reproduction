#!/usr/bin/env bash
set -euo pipefail
RUNTIME=/opt/3dgs-runtime
source "$RUNTIME/miniconda3/etc/profile.d/conda.sh"
export CONDA_PKGS_DIRS="$RUNTIME/pkgs" TMPDIR="$RUNTIME/tmp" PIP_CACHE_DIR="$RUNTIME/pip-cache" PYTHONNOUSERSITE=1
if [ ! -x "$RUNTIME/envs/neuralsound/bin/python" ]; then
  conda create -y -p "$RUNTIME/envs/neuralsound" --clone "$RUNTIME/envs/physgaussian"
fi
conda activate "$RUNTIME/envs/neuralsound"
export CUDA_HOME="$CONDA_PREFIX" MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.6 OMP_NUM_THREADS=2
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"
export LIBRARY_PATH="/usr/lib/wsl/lib:$CONDA_PREFIX/lib:${LIBRARY_PATH:-}"
conda install -y --freeze-installed --override-channels --strict-channel-priority -c nvidia/label/cuda-11.8.0 -c conda-forge numpy=1.24 scipy=1.10 cuda-cudart=11.8 cuda-nvcc=11.8 cuda-nvtx=11.8 cuda-profiler-api=11.8 cuda-cccl=11.8 libcurand-dev=10.3 libcusolver-dev=11.4 libcublas-dev=11.11 libcusparse-dev=11.7 libcublas=11.11 libcusparse=11.7 openblas pyopencl pocl
python -m pip install torch-scatter --only-binary=:all: -f https://data.pyg.org/whl/torch-2.0.0+cu118.html
python -m pip install bempp-cl==0.2.4 plotly gmsh tensorboard meshio
PROJECT=$(cd "$(dirname "$0")/../.." && pwd)
# Compile on the Linux filesystem; keep the upstream checkout untouched.
mkdir -p "$RUNTIME/build/MinkowskiEngine"
cp -a "$PROJECT/03_NeuralSound/code/MinkowskiEngine/." "$RUNTIME/build/MinkowskiEngine/"
cd "$RUNTIME/build/MinkowskiEngine"
python setup.py install --force_cuda --blas=openblas --blas_include_dirs="$CONDA_PREFIX/include" --blas_library_dirs="$CONDA_PREFIX/lib"
python -m pip install pycuda==2022.2.2
python -c 'import torch,torch_scatter,MinkowskiEngine,bempp.api,pyopencl; print(torch.__version__,MinkowskiEngine.__version__,pyopencl.get_platforms())'
python -m pip check
