# PhysGaussian 复现记录

日期：2026-11-01，Asia/Shanghai。已运行官方 CUDA MPM 与高斯协方差核；包括合成梁对照和官方 Ficus 模型短时仿真。**没有完成原始透视 SH 渲染流程或论文结果复现。**

## 论文、代码与来源

论文：[PhysGaussian 2024](../paper/PhysGaussian_2024.pdf)。官方仓库 <https://github.com/XPandora/PhysGaussian>，本地为 `../code/PhysGaussian/`。

锁定提交：

- PhysGaussian：`8339ed6aa2cd5d50e1001a254a3d95aea678a956`。
- gaussian-splatting：`d9fad7b3450bf4bd29316315032d57157e23a515`。
- diff-gaussian-rasterization：`59f5f77e3ddbac3ed9db93ec2cfe99ed6c5d121d`。
- simple-knn：`44f764299fa305faf6ec5ebd99939e0508331503`。
- glm：`5c46b9c07008ae65cb81ab79cd677ecc1934b903`。
- SIBR_viewers：`4ae964a267cd7a844d9766563cf9d0b500131a22`。

已递归拉取子模块。最终检查三个主上游仓库的跟踪文件未修改；本地输入、适配、验证与渲染器全部放在原仓库外。保留上游许可文件与声明；未在 PhysGaussian 顶层找到独立许可文件，不据此假定可任意再分发。gaussian-splatting 及其子模块许可应分别查看原目录。

## 环境与兼容适配

项目内 Conda：`F:/System/Desktop/3DGS/复现/.conda/physgaussian`。Python 3.11.18、NumPy 1.24.3、Warp 0.10.1、torch 2.0.0+cpu、h5py 3.10.0、Matplotlib 3.10.9。torch CPU 包满足作者模块的导入；实际物理步进为 Warp 的 `cuda:0`，不是 CPU 物理仿真。

Warp 自带 NVRTC 可编译物理核，无须用系统 nvcc。但 NVRTC 11.5 无法正确打开包含中文的 include 路径，出现 `cannot open source file builtin.h`，文件实际存在。

处理方式：

1. 创建目录联接 `C:/Users/LENOVO/.cache/3dgs-physgaussian` → 项目 Conda 环境，不复制环境。
2. 仅联接仍失败，因为 Warp 的 `build_cuda` 会通过 `realpath` 还原中文路径。
3. `../code/warp_windows_compat.py` 在运行时替换该构建函数，保留 Warp 0.10.1 的编译标志与 native 调用，只让 include 参数保留 ASCII 联接路径。没有编辑安装包或作者源码。
4. 适配器限定 Warp 0.10.1，入口检查联接目标，防止误用其他环境。同一用户有多个工作区时应明确联接对应哪个工作区。

当前 Windows 用户目录是 ASCII。迁移到含非 ASCII 用户名的机器时，此适配路径需要重新选择。

完整导出见 [environment.yml](environment.yml)、[Conda 显式包清单](conda-explicit-win64.txt)、[pip 锁定清单](requirements-lock.txt)。恢复方法见 [ENVIRONMENT.md](ENVIRONMENT.md)。这些是已运行模块的环境，不是原始端到端渲染环境。两个项目 Conda 环境的 `pip check` 均通过。

## 实验一：合成高斯梁

入口 `../code/run_mpm.py` 使用未修改的 `MPM_Simulator_WARP`、`compute_cov_from_F` 与官方核。

192 个材料点，32³ 网格，网格域 1 m，初始点间距 0.025 m；每粒子体积为间距立方，密度 1000 kg/m³，总质量 3 kg。jelly 材料，ν=0.3，E 分别为 20/80 kPa；重力 -9.81 m/s²，左侧网格固定，dt=0.0002 s，各 2000 步，共 0.4 s。输入和相机是本地合成，非论文场景。

验证包括零重力静止、无约束自由落体与离散解析解、独立 NumPy 的 FΣ₀Fᵀ、协方差正定、变形未翻转和质量守恒。自由落体平均位置误差 2.344e-7 m；协方差最大相对误差 8.393e-8。软/硬梁最大端部下挠分别为 0.256964/0.147108 m，支持本场景下的刚度趋势，不是梁连续体解析精度验证。

见 [RESULTS.md](RESULTS.md)、[mpm-metrics.json](mpm-metrics.json)。输出位于 `../outputs/mpm_gaussians/`，包含软/硬 GIF、最终帧、位移图和每帧状态 NPZ。动画是本地正交各向异性高斯 alpha 合成，没有原透视相机、完整 SH、外观训练或 CUDA 光栅器。

## 实验二：官方 Ficus

模型来自作者 README 下载脚本：<https://drive.google.com/uc?id=1zic8PNxUsYESyrVZ8Ywy-FxpmQ01PGpe>。下载压缩包保留在 `../outputs/ficus_whitebg-trained.zip`；所需 PLY、相机和配置解压到 `../inputs/ficus_whitebg-trained/`。PLY SHA256：`a757dd2e92f578e87b53e873670c6333d024a5dd496399797438a7d0f13fd242`。

原始 203930 个高斯，按官方 opacity>0.02 保留 166894 个，全部参与仿真。用官方 Ficus 配置的 E=2 MPa、ν=0.4、主体/上部密度 200/70、零重力、固定底部、逐粒子单步外力 [-0.18,0,0] 以及 0.9999 网格速度阻尼。不要把逐粒子力误写成全模型总力。

50³ 网格，域 [0,2]³，dt=1e-4 s；运行 1200 步（0.12 s），原设置是 5 s。NumPy 实现与当前配置相对应的包围盒中心归一化、四元数协方差、每网格单元体积按粒子数分配；替代原入口中硬编码 CUDA/Taichi 的预处理。此配置没有内部填充。以上是对当前零旋转 Ficus 配置的适配，不能直接视为所有配置的通用替代。

最大位置变化 0.099809（归一化模拟坐标），采样协方差公式误差 1.101e-8；全量位置、F、Σ 均有限，质量不变。协方差公式比较只抽取显示子集，不声称逐粒子全部做了独立公式检验。固定随机种子 20261101 抽取 6000 个高斯做诊断显示，不减少物理粒子数。13 帧 GIF 使用 100 ms/帧，播放为慢动作，不代表实时模拟速度。

见 [FICUS_RESULTS.md](FICUS_RESULTS.md)、[ficus-metrics.json](ficus-metrics.json) 和 `../outputs/ficus_short/`。全量初末状态保存为 `all_gaussians_initial_final.npz`；显示子集轨迹单独保存。已目视检查初末图像，植株和花盆可辨，显示为抽样后的诊断画质。GPU 检查点总占用约 196 MiB，包含驱动与其他进程，非精确进程峰值；29.2 s 单次运行耗时也不作为论文基准。

## 执行命令与失败记录

从项目根目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\01_PhysGaussian\run.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\01_PhysGaussian\run_ficus.ps1
```

入口隔离用户 site-packages 并设置 UTF-8；第二个入口依赖第一个准备的环境联接。成功日志为 `../logs/mpm.log` 与 `../logs/ficus.log`。

保留的失败及解决状态：

- `mpm-initial-import-failure.log`：初始化函数导入位置错误，包装器已改为 `warp_utils`。
- `mpm-unicode-include-failure.log`、`mpm-junction-only-failure.log`：中文 include 与 realpath 问题，采用上述运行时适配解决。
- `mpm-version-check-failure.log`：Warp 0.10.1 无 `__version__`，改用标准包 metadata。
- `original-rasterizer-build.log`：torch 2.0 与 setuptools 84 的 `pkg_resources` 不兼容；环境内固定 setuptools 69.5.1 解决，见 `setuptools-compat-install.log`。
- `original-rasterizer-build-after-setuptools.log`：重新实际尝试原光栅器构建，报 `CUDA_HOME environment variable is not set`。PATH 未发现 nvcc，当前 torch 为 CPU 包；尚未安装匹配的 CUDA PyTorch、Toolkit/nvcc 与 C++ 编译链，原渲染器未编译成功。

构建尝试使用该 Conda Python 执行 `-m pip install --no-deps --no-build-isolation -e ./01_PhysGaussian/code/PhysGaussian/gaussian-splatting/submodules/diff-gaussian-rasterization`。错误日志完整保留，不把安装失败称为运行成功。Windows PowerShell 对 pip stderr 的展示可能出现 NativeCommandError，应结合实际 Python 退出码与导入检查判断。

## 仍需完成

配置独立完整渲染环境，匹配 CUDA PyTorch、CUDA Toolkit/nvcc 和宿主编译器，构建原 diff-gaussian-rasterization 与 simple-knn，并补齐 gs_simulation 其余依赖；随后以原相机、SH 和完整高斯运行 5 s Ficus，核对输出。尚未验证其他材料、塑性/断裂、内部填充、重建训练或论文全部场景。还没有与 PAT 或 NeuralSound 的声音形成同一物体的视觉声学联动。
