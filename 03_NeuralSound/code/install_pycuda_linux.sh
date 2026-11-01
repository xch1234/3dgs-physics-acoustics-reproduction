#!/usr/bin/env bash
set -euo pipefail
source /opt/3dgs-runtime/miniconda3/etc/profile.d/conda.sh
conda activate /opt/3dgs-runtime/envs/neuralsound
export CUDA_HOME="$CONDA_PREFIX" PYTHONNOUSERSITE=1
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"
export LIBRARY_PATH="/usr/lib/wsl/lib:$CONDA_PREFIX/lib:${LIBRARY_PATH:-}"
export TMPDIR=/opt/3dgs-runtime/tmp PIP_CACHE_DIR=/opt/3dgs-runtime/pip-cache
python -m pip install --no-build-isolation pycuda==2022.2.2
python -c 'import pycuda.autoinit; import pycuda.driver as d; print(d.Device(0).name())'
