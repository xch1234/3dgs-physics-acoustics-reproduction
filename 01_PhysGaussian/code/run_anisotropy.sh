#!/usr/bin/env bash
set -euo pipefail
project=$(cd "$(dirname "$0")/.." && pwd)
runtime=/opt/3dgs-runtime/envs/physgaussian
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2
export CUDA_HOME="$runtime" PATH="$runtime/bin:$PATH"
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:$runtime/lib:${LD_LIBRARY_PATH:-}"
export TORCH_HOME=/opt/3dgs-runtime/torch-cache
# Existing source alias is read only; do not recreate links outside the workspace.
test -f /opt/3dgs-runtime/PhysGaussian-source/gs_simulation.py
export PHYSGAUSSIAN_SOURCE=/opt/3dgs-runtime/PhysGaussian-source
exec "$runtime/bin/python" -u "$project/code/run_anisotropy.py" "$@"
