#!/usr/bin/env bash
set -euo pipefail
project=$(cd "$(dirname "$0")/.." && pwd)
headers=/opt/3dgs-runtime/envs/pat-tools/include
eigen="$project/code/dependencies/eigen-git-mirror-3.3.7"
test -f "$headers/gsl/gsl_sf.h"
test -f "$eigen/Eigen/Dense"
mkdir -p "$project/outputs/modalsound_transfer"
g++ -O2 -std=c++14 -I"$headers" -I"$eigen" -I"$project/code/ModalSound/ModalSound/src" \
  "$project/code/validate_modalsound_transfer.cpp" \
  "$project/code/ModalSound/ModalSound/src/generic/precision_type.cpp" \
  -L/opt/3dgs-runtime/envs/pat-tools/lib -Wl,-rpath,/opt/3dgs-runtime/envs/pat-tools/lib \
  -lgsl -lgslcblas -o "$project/outputs/modalsound_transfer/evaluate_transfer"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
exec /opt/3dgs-runtime/envs/physgaussian/bin/python -u "$project/code/run_modalsound_transfer.py"
