#!/usr/bin/env bash
# Reproduce the additional paper-scope experiments using existing Conda envs.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
mode=${1:-all}
case "$mode" in all|validation-only) ;; *) exit 2;; esac
phys=/opt/3dgs-runtime/envs/physgaussian
neural=/opt/3dgs-runtime/envs/neuralsound
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2
export MPLCONFIGDIR="$root/reproduction/cache/matplotlib" CUDA_CACHE_PATH="$root/reproduction/cache/cuda"
export TMPDIR="$root/reproduction/cache/tmp" PYCUDA_CACHE_DIR="$root/reproduction/cache/pycuda"
export TORCH_EXTENSIONS_DIR="$root/reproduction/cache/torch_extensions"
mkdir -p "$MPLCONFIGDIR" "$CUDA_CACHE_PATH" "$TMPDIR" "$PYCUDA_CACHE_DIR" "$TORCH_EXTENSIONS_DIR"
if [ "$mode" = all ]; then
  bash --noprofile --norc "$root/01_PhysGaussian/code/run_transport_audit.sh"
  bash --noprofile --norc "$root/02_PAT/code/run_modalsound_transfer.sh"
  bash --noprofile --norc "$root/03_NeuralSound/code/run_paper_schedule.sh" vibration
  bash --noprofile --norc "$root/03_NeuralSound/code/run_paper_schedule.sh" radiation --optimizer cpu_adam
  bash --noprofile --norc "$root/01_PhysGaussian/code/run_anisotropy.sh"
  "$phys/bin/python" -u "$root/reproduction/finish_corrected_scenes.py" --wait-pid 0
fi
export CUDA_HOME="$neural" LD_LIBRARY_PATH="/usr/lib/wsl/lib:$neural/lib"
export PATH="$neural/bin:$PATH"
"$neural/bin/python" -u "$root/03_NeuralSound/code/export_radiation_predictions.py" --paper-schedule
"$neural/bin/python" -u "$root/reproduction/check_training_checkpoints.py" --paper-schedule
"$neural/bin/python" -u "$root/reproduction/audit_vibration_arrays.py" --paper-schedule
export PATH="$phys/bin:$PATH"
"$phys/bin/python" -u "$root/01_PhysGaussian/code/summarize_official_scenes.py"
"$phys/bin/python" -u "$root/reproduction/write_scope_extension_reports.py"
