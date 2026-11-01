#!/usr/bin/env bash
set -euo pipefail
RUNTIME=/opt/3dgs-runtime
mkdir -p "$RUNTIME/downloads" "$RUNTIME/tmp" "$RUNTIME/pip-cache"
export TMPDIR="$RUNTIME/tmp" PIP_CACHE_DIR="$RUNTIME/pip-cache" CONDA_PKGS_DIRS="$RUNTIME/pkgs"
export PYTHONNOUSERSITE=1
if [ ! -x "$RUNTIME/miniconda3/bin/conda" ]; then
  if [ -f /mnt/f/3dgs-runtime/downloads/Miniconda3-Linux-x86_64.sh ]; then
    cp /mnt/f/3dgs-runtime/downloads/Miniconda3-Linux-x86_64.sh "$RUNTIME/downloads/Miniconda3-Linux-x86_64.sh"
  else
    curl -fL --retry 3 --speed-time 30 --speed-limit 1024 https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py39_24.3.0-0-Linux-x86_64.sh -o "$RUNTIME/downloads/Miniconda3-Linux-x86_64.sh"
  fi
  bash "$RUNTIME/downloads/Miniconda3-Linux-x86_64.sh" -b -p "$RUNTIME/miniconda3"
fi
"$RUNTIME/miniconda3/bin/conda" create -y -p "$RUNTIME/envs/physgaussian" --override-channels --strict-channel-priority -c nvidia/label/cuda-11.8.0 -c conda-forge python=3.9 pip numpy=1.24 scipy=1.10 cuda-nvcc=11.8 cuda-cudart=11.8 cuda-cudart-dev=11.8 cuda-cccl=11.8 libcusparse=11.7 libcusparse-dev=11.7 libcublas=11.11 libcublas-dev=11.11 openblas ninja ffmpeg
source "$RUNTIME/miniconda3/etc/profile.d/conda.sh"
conda activate "$RUNTIME/envs/physgaussian"
python -m pip install torch==2.0.0+cu118 torchvision==0.15.1+cu118 --index-url https://download.pytorch.org/whl/cu118
python -m pip install setuptools==69.5.1 wheel h5py==3.10.0 opencv-python-headless==4.9.0.80 Pillow==10.2.0 plyfile==1.0.3 PyMCubes==0.1.4 pymeshlab==2023.12.post1 taichi==1.5.0 tqdm==4.66.1 warp-lang==0.10.1 matplotlib==3.8.4 numba==0.58.1 tensorboard meshio psutil
python -m pip check
nvcc --version
python -c 'import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))'
