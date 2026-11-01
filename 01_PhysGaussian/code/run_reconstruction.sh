#!/usr/bin/env bash
set -euo pipefail
source /opt/3dgs-runtime/miniconda3/etc/profile.d/conda.sh
conda activate /opt/3dgs-runtime/envs/physgaussian
export PYTHONNOUSERSITE=1 OMP_NUM_THREADS=2 CUDA_HOME="$CONDA_PREFIX"
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"
export TORCH_HOME=/opt/3dgs-runtime/torch-cache
exec python -u "$(dirname "$0")/run_reconstruction.py" "$@"
