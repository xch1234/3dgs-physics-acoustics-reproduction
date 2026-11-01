#!/usr/bin/env bash
set -euo pipefail
source /opt/3dgs-runtime/miniconda3/etc/profile.d/conda.sh
export CONDA_PKGS_DIRS=/opt/3dgs-runtime/pkgs
ENVROOT=/opt/3dgs-runtime/envs/pat-tools
if [ ! -f "$ENVROOT/include/gsl/gsl_sf.h" ]; then
  conda create -y -p "$ENVROOT" --override-channels -c conda-forge gsl=2.7
fi
PROJECT=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$PROJECT/outputs/modalsound_basis"
g++ -O2 -std=c++14 -I"$ENVROOT/include" -I"$PROJECT/code/ModalSound/ModalSound/src" \
  "$PROJECT/code/validate_modalsound_basis.cpp" -L"$ENVROOT/lib" -Wl,-rpath,"$ENVROOT/lib" \
  -lgsl -lgslcblas -o "$PROJECT/outputs/modalsound_basis/evaluate_basis"
"$PROJECT/outputs/modalsound_basis/evaluate_basis" > "$PROJECT/outputs/modalsound_basis/basis.txt"
