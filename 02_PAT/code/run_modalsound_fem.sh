#!/usr/bin/env bash
set -euo pipefail
project=$(cd "$(dirname "$0")/.." && pwd)
headers=/opt/3dgs-runtime/envs/pat-tools/include
test -f "$headers/boost/multi_array.hpp"
mkdir -p "$project/outputs/modalsound_fem"
g++ -O2 -std=c++14 -I"$headers" -I"$project/code/ModalSound/ModalSound/src" \
  "$project/code/validate_modalsound_fem.cpp" \
  "$project/code/ModalSound/ModalSound/src/deformable/stvk.cpp" \
  "$project/code/ModalSound/ModalSound/src/generic/precision_type.cpp" \
  -o "$project/outputs/modalsound_fem/assemble_fem"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
exec /opt/3dgs-runtime/envs/physgaussian/bin/python -u "$project/code/run_modalsound_fem.py"
