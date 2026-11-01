#!/usr/bin/env bash
set -euo pipefail
project=$(cd "$(dirname "$0")/.." && pwd)
task=${1:?Specify vibration or radiation}
shift
case "$task" in vibration|radiation) ;; *) exit 2;; esac
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2
export CUDA_HOME=/opt/3dgs-runtime/envs/neuralsound
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:$CUDA_HOME/lib:${LD_LIBRARY_PATH:-}"
export MPLCONFIGDIR="$project/../reproduction/cache/matplotlib"
export CUDA_CACHE_PATH="$project/../reproduction/cache/cuda"
exec "$CUDA_HOME/bin/python" -u "$project/code/train_$task.py" --paper-schedule "$@"
