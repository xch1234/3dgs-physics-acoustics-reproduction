#!/usr/bin/env bash
set -euo pipefail
RUNTIME=/opt/3dgs-runtime
source "$RUNTIME/miniconda3/etc/profile.d/conda.sh"
conda activate "$RUNTIME/envs/physgaussian"
export CUDA_HOME="$CONDA_PREFIX" MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.6
export PYTHONNOUSERSITE=1 TMPDIR="$RUNTIME/tmp" PIP_CACHE_DIR="$RUNTIME/pip-cache"
PROJECT=$(cd "$(dirname "$0")/../.." && pwd)
python -m pip install --no-build-isolation --no-deps "$PROJECT/01_PhysGaussian/code/PhysGaussian/gaussian-splatting/submodules/diff-gaussian-rasterization"
python -m pip install --no-build-isolation --no-deps "$PROJECT/01_PhysGaussian/code/PhysGaussian/gaussian-splatting/submodules/simple-knn"
python -c 'import diff_gaussian_rasterization, simple_knn._C; print("CUDA rasterizer and KNN imports passed")'
