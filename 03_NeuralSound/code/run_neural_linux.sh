#!/usr/bin/env bash
set -euo pipefail
source /opt/3dgs-runtime/miniconda3/etc/profile.d/conda.sh
conda activate /opt/3dgs-runtime/envs/neuralsound
export CUDA_HOME="$CONDA_PREFIX" PYTHONNOUSERSITE=1 OMP_NUM_THREADS=2
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"
export LIBRARY_PATH="/usr/lib/wsl/lib:$CONDA_PREFIX/lib:${LIBRARY_PATH:-}"
task=${1:?Specify vibration or radiation}
shift
case "$task" in
  vibration) exec python -u "$(dirname "$0")/train_vibration.py" "$@";;
  radiation) exec python -u "$(dirname "$0")/train_radiation.py" "$@";;
  bem) exec python -u "$(dirname "$0")/validate_official_bem.py" "$@";;
  example) exec python -u "$(dirname "$0")/run_official_example.py" "$@";;
  labels) exec python -u "$(dirname "$0")/generate_official_labels.py" "$@";;
  audio) exec python -u "$(dirname "$0")/run_neural_audio.py" "$@";;
  benchmark) exec python -u "$(dirname "$0")/benchmark_vibration.py" "$@";;
  example_labels) exec python -u "$(dirname "$0")/run_example_acoustics.py" --prepare "$@";;
  example_radiation) exec python -u "$(dirname "$0")/run_example_acoustics.py" --predict "$@";;
  example_hybrid) exec python -u "$(dirname "$0")/run_example_hybrid.py" "$@";;
  predictions) exec python -u "$(dirname "$0")/export_radiation_predictions.py" "$@";;
  *) echo "Unknown task: $task" >&2; exit 2;;
esac
