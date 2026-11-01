#!/usr/bin/env bash
set -euo pipefail
source /opt/3dgs-runtime/miniconda3/etc/profile.d/conda.sh
conda activate /opt/3dgs-runtime/envs/physgaussian
export CUDA_HOME="$CONDA_PREFIX" PYTHONNOUSERSITE=1 OMP_NUM_THREADS=1
export PATH="$CONDA_PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"
# Warp 0.10 writes generated CUDA as ASCII, including source-path comments.
PROJECT=$(cd "$(dirname "$0")/../.." && pwd)
ln -sfn "$PROJECT/01_PhysGaussian/code/PhysGaussian" /opt/3dgs-runtime/PhysGaussian-source
export PHYSGAUSSIAN_SOURCE=/opt/3dgs-runtime/PhysGaussian-source
exec python -u "$(dirname "$0")/run_official_linux.py" "$@"
