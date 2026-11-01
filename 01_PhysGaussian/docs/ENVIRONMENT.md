# Conda 环境恢复说明

2026-11-01 更新：下文记录早期 Windows 基础验证环境。完整 PhysGaussian CUDA 渲染、3DGS 训练和 NeuralSound 神经训练已经在独立 WSL Conda 环境运行，当前环境与重跑入口请先看 [统一环境说明](../../复跑与环境说明.md)。这里的 CPU Torch 环境不能用于完整重建训练，也不应覆盖已安装的 Linux 环境。

当前本机环境已经安装，直接使用项目入口即可。以下用于迁移或重建，不应对现有环境无目的重装。

## PhysGaussian 已运行模块

在项目根目录，使用自己的 Conda 可执行路径。此次本机路径为 `C:/ProgramData/anaconda3/Scripts/conda.exe`。

```powershell
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' create -p .\.conda\physgaussian python=3.11.18 pip -y
$env:PYTHONNOUSERSITE='1'
& '.\.conda\physgaussian\python.exe' -m pip install --extra-index-url https://download.pytorch.org/whl/cpu -r .\01_PhysGaussian\docs\requirements-lock.txt
& '.\.conda\physgaussian\python.exe' -m pip check
powershell -NoProfile -ExecutionPolicy Bypass -File .\01_PhysGaussian\run.ps1
```

需要 NVIDIA GPU 与可用驱动，Warp 0.10.1 自带运行时编译库。锁定清单包含 `torch==2.0.0+cpu`，因此需要上面的 PyTorch CPU 索引。setuptools 69.5.1 为旧 torch 构建工具的兼容版本。原始 `pip freeze --all` 保留在 `pip-freeze-raw.txt`；其中 Conda 打包的 pip 指向构建机临时路径，迁移清单已替换为实际版本 `pip==26.2.2`。

`environment.yml` 是 Conda 自动导出的审计快照，含本机绝对 prefix；迁移时显式指定新 prefix。`conda-explicit-win64.txt` 只描述 Conda 层，不含 pip 包；若用它恢复，仍须安装 pip 锁定清单。曾用 pip 覆盖 Conda 自带 setuptools，Conda 原始包清单可能仍记录原安装版本，以 `requirements-lock.txt` 和实际 importlib.metadata 结果为准。不要将该清单当成原始渲染器的完整环境。

## PAT / NeuralSound 数值模块

共用项目内 `.conda/acoustics`，不污染 base。可用 `02_PAT/docs/conda-explicit-win64.txt` 或 `03_NeuralSound/docs/conda-explicit-win64.txt` 在 Windows 64 位恢复；两者来自同一已运行环境：

```powershell
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' create -p .\.conda\acoustics --file .\02_PAT\docs\conda-explicit-win64.txt -y
powershell -NoProfile -ExecutionPolicy Bypass -File .\03_NeuralSound\run.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\02_PAT\run.ps1
```

这不是 NeuralSound 完整神经环境；后者已安装在 WSL `/opt/3dgs-runtime/envs/neuralsound`，包含 MinkowskiEngine、torch-scatter、PyCUDA、Bempp-cl 等。本项目使用自行训练并保存的权重，未取得作者匹配的预训练权重。
