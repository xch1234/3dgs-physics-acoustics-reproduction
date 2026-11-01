#!/usr/bin/env bash
set -euo pipefail
project=$(cd "$(dirname "$0")/.." && pwd)
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:/opt/3dgs-runtime/envs/physgaussian/lib:${LD_LIBRARY_PATH:-}"
exec /opt/3dgs-runtime/envs/physgaussian/bin/python -u "$project/code/validate_gaussian_transport.py"
