#!/usr/bin/env bash
set -euo pipefail
source /opt/3dgs-runtime/miniconda3/etc/profile.d/conda.sh
project_root=$(cd "$(dirname "$0")/.." && pwd)
for item in 'physgaussian:01_PhysGaussian' 'neuralsound:03_NeuralSound' 'pat-tools:02_PAT'; do
  environment_name=${item%%:*}
  folder=${item#*:}
  environment_prefix=/opt/3dgs-runtime/envs/$environment_name
  conda list -p "$environment_prefix" --explicit > "$project_root/$folder/docs/conda-explicit-linux64.txt"
  conda env export -p "$environment_prefix" > "$project_root/$folder/docs/environment-linux.yml"
  if [ -x "$environment_prefix/bin/python" ]; then
    "$environment_prefix/bin/python" -m pip freeze > "$project_root/$folder/docs/requirements-linux-lock.txt"
    "$environment_prefix/bin/python" -m pip check > "$project_root/$folder/docs/pip-check-linux.txt"
  fi
done
uname -a > "$project_root/reproduction/linux-system.txt"
nvidia-smi > "$project_root/reproduction/nvidia-smi-final.txt"
gcc --version > "$project_root/reproduction/gcc-version.txt"
