# 官方实现可行性核查

核查日期：2026-10-31（Asia/Shanghai）。结论针对下列具体提交与本次公开资源检索，不推断所有历史版本或未公开资源。

## 结论与路线选择

优先完成自建 CPU 模态声音原理实验，并尝试运行 NeuralSound 官方传统 FEM 模块。当前没有满足官方神经网络推理所需的权重、配套样例与完整环境，因此不进入 B1，不启动从零训练。

## A0 / A2：ModalSound 教学代码

- 仓库：<https://github.com/cxzheng/ModalSound>。
- 本地路径：`reproduction/vendor/ModalSound`。
- 提交：`1af5e40893d0ad1b73b594a0cba7a5466b4fc56d`。
- 顶层许可证为 GPLv3；IsoStuffer 另附 COPYING / COPYING.LESSER，使用时应保留各自声明。
- 根 README 明确它是 SIGGRAPH 2016 教学代码，不是已经核实的 PAT 2006 原始完整实现。
- `ModalSound/README.md` 的 Input & Output 部分仍为 “To be updated”；编译说明以 Ubuntu 16.04、旧 MKL、GNU 编译器为例，Windows 未验证。
- `ModalSound/CMakeLists.txt` 要求 MKL、Boost、GSL；图形演示还涉及 Qt、QGLViewer、OpenGL 等。其他依赖包括 Eigen、protobuf、libconfig 等。
- 当前 Windows 的 PATH 未找到 cmake 或 nvcc；Ubuntu1 有 g++，未在 PATH 找到 cmake、nvcc 或 conda。未安装这套旧 C++ 图形依赖，也未宣称构建失败。
- 已跟踪样例仅找到 `IsoStuffer/sample-mesh/spot_triangulated.obj`；它是四面体化输入，不能直接替代完整的声音样例。未找到已跟踪的 `.tet`、声学 `.dat` 或 `.pbuf` 文件。

**声学求解链的关键证据：**

- `ModalSound/src/transfer/BoundaryIntegralTransfer.hpp` 注释明确输入是 FastBEM 的输入与输出文件；边界声压从 FastBEM 输出读取。
- `ModalSound/src/protobuf/gen_moments.cpp` 的工具接收 `[fbem input file] [fbem output file]`，再调用 `compute_moments()` 生成 `moments.dat` / `moments.pbuf`。
- 因而仓库不只是读取多极子系数，它确实包含从已有 BEM 结果计算系数的代码；但这不等于包含生成边界声压的完整 FastBEM 求解器。
- 本次没有找到完整外部求解器和可运行的匹配数据链。A2 停在缺失资源核查，不伪造系数、不把单极子近似标成 PAT。

原始文件清单：`ModalSound-tracked-files.txt`。可直接对照本地保留的上游源代码。

## B0：NeuralSound

- 项目页：<https://hellojxt.github.io/NeuralSound/>。
- 仓库：<https://github.com/hellojxt/NeuralSound>。
- 提交：`b18e81b1e3dba7e963b09a7d9a45b584707d805f`。
- 本次跟踪文件列表未找到顶层 LICENSE。此为资源记录，不等于推断作者未授予任何许可。

### 权重、网络、数据与入口

1. 已检查根 README、`environment.md`、整个提交的跟踪文件、项目页、Releases 及当前全部三条 issue/PR 条目。
2. 跟踪文件中未发现 `.pt`、`.pth`、`.ckpt`，Releases API 返回空数组；项目页未找到权重下载链接。README 的 `weights/default_tag.pt` 指训练产物路径，不是预训练下载地址。结论是“在已核查公开资源中未找到”，不能推断作者手中没有权重。
3. 提供 `dataset/mesh/example.obj`，但未提供已跟踪的 `.npy` 体素、`.npz` 模态/FFAT 输入或已打包的推理样例。体素生成链涉及 PyCUDA。
4. 网络定义存在，包括 `src/net/acousticnet.py`、`src/net/eigennet.py` 及稀疏卷积 U-Net 文件；训练脚本存在。
5. 归一化规则部分明确写在 `acoustic/dataset.py`：输入模态特征除以 RMS，坐标变换 `(coords/16-1)/0.5`，波数按 20–20000 Hz 区间归一化；输出图还按自身 RMS 归一化，幅值标签为 `(log(RMS)+8)/3`。不能把这解释成已取得某个 checkpoint 的配套推理配置。
6. 未找到文档支持的一键预训练推理入口。`trainer_template.py` 含本地权重加载逻辑，但缺少可下载的匹配权重。
7. README 明确公开声辐射网络比论文原架构更紧凑，因此即使以后获得权重也必须标明版本。

### 运行环境

- 作者测试配置：Ubuntu 20.04、Python 3.7、CUDA 11.1；PyTorch 1.10.0、MinkowskiEngine、torch-scatter、PyCUDA、Bempp-cl 等。
- 本机 WSL2 Ubuntu1 确实可用，为 Ubuntu 20.04.3，GPU 能被 WSL 的 nvidia-smi 识别。
- 默认登录 shell 因已有 profile 中的路径导出报 `export: Files/Common: bad variable name`；使用 `bash --noprofile --norc` 可绕过。没有修改用户 shell 配置。
- nvcc / Linux conda 未在本次非登录 PATH 找到，未核实其他路径是否存在完整 CUDA 工具链。
- Windows 驱动 595.95；nvidia-smi 所示 CUDA 13.2 是驱动支持能力，不代表已安装 CUDA Toolkit 13.2。
- 本次在项目内 Conda 环境运行 Python 3.11 的 CPU 数值模块；这不是作者完整神经网络环境。4GB 显存能否完成神经推理未实测。
- 已记录内存/磁盘/GPU 快照；初始可用内存约 2.27GiB，因此 CPU 实验限制库线程为 1。

### 相关问题与 B2 路线

- <https://github.com/hellojxt/NeuralSound/issues/2> 报告 torch.lobpcg 收敛断言与 `n < 3k` 的小模型限制；当前无回复。
- <https://github.com/hellojxt/NeuralSound/pull/3> 为 mel limits 修正，不提供权重。
- B2 使用官方 `src/classic/fem/assembler.py`、`femModel.py` 与 `solver.py` 中的 Lanczos 路径。它们可避开 PyTorch、MinkowskiEngine、PyCUDA 和 BEM，只需 NumPy、SciPy、Numba。
- 本地包装脚本生成一个小体素梁，固定一端后调用原 Lanczos 求解器。约束后的刚度矩阵正定，避免原 `sigma=0` 求解器直接分解自由体奇异刚度矩阵。
- 该实验属于“官方传统数值模块复现”，并非论文的神经混合求解器。结果及数值检查见 `../neuralsound/outputs/RESULTS.zh-CN.md`（成功运行后生成）。

### 保留的证据

- `neuralsound-project.html`：项目页快照。
- `neuralsound-releases.json`：Releases API 原始响应。
- `neuralsound-issues.json`：全部当前 issue/PR 条目。
- `neuralsound-contents.json`、`NeuralSound-tracked-files.txt`：目录与文件清单。
- `machine.json`、`wsl-check.txt`：机器与 WSL 核查记录。
- `../logs/`：环境安装和实际运行日志。

## 距离完整声辐射 / 3DGS 联动还缺什么

需要明确的几何与材料输入、3DGS 到物理离散模型的映射、碰撞/交互外力、可验证的模态求解、声辐射传递求解或匹配的训练权重，以及随听者位置变化的声音合成与同步接口。本次两个小实验只覆盖其中的振动基础和官方数值模块，尚未打通完整流程。
