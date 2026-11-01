# 复现执行状态

> 历史阶段记录（2026-10-31）。2026-11-01 的当前结果已迁入三个论文文件夹，见 [复现总报告](../复现总报告.md)。本轮已新增 PAT BEM/多极子音频及 PhysGaussian 官方 GPU 物理/Ficus 短时仿真；下文“尚未完成 A2 / 未运行 GPU”等仅适用于当时。原始数据保留。

更新：2026-10-31（Asia/Shanghai）。已完成计划的最低交付，并额外跑通 NeuralSound 官方传统 FEM 模块。

## 完成情况

- A0 已完成：缺少匹配的 FastBEM 结果 / 声学系数样例，未构建旧 C++ 图形工具链；见 `audit/FEASIBILITY.zh-CN.md`。
- A1 已完成：五组 WAV、串联试听、原始数据与两张图已生成；闭式频率、独立 ODE、能量、残差、音频回读检查通过。
- B0 已完成：已核查公开项目页、仓库、Releases、issues，未找到可下载预训练权重；B1 门槛未满足。
- B2 已完成：使用未修改的官方 FEM 组装与 Lanczos，搭配本地生成体素梁和固定端适配；总质量、刚体模态、残差、稠密参考及参数缩放检查全部通过。
- 环境：`.conda/acoustics` 已完成安装。Conda 为 Numba 调整了该独立环境的 NumPy / SciPy 版本，两条路线已在最终环境重新运行成功。
- 尚未完成：A2 的 PAT 声辐射、B1 神经网络推理、论文精度/速度复现、3DGS 联动。A2 缺少匹配 FastBEM 结果和完整样例链；B1 未取得公开可下载的匹配权重及完整环境。未启动训练或整个 ABC 数据集下载。

## 已核实

- 本目录此前没有复现代码和 STATUS 记录。
- Windows；RTX 2050 4GB；物理内存约 15.67GiB，初始空闲约 2.27GiB。
- WSL2 的 Ubuntu1 为 Ubuntu 20.04.3；使用不加载 profile 的 bash 可正常运行，GPU 可见。
- Ubuntu1 的登录 shell 存在 `export: Files/Common: bad variable name`，暂通过 `bash --noprofile --norc` 绕过，未修改用户配置。
- 本次数值实验使用 CPU 单线程；没有运行 GPU 实验，没有关闭用户游戏或进程。

## 上游版本

- ModalSound：`1af5e40893d0ad1b73b594a0cba7a5466b4fc56d`。
- NeuralSound：`b18e81b1e3dba7e963b09a7d9a45b584707d805f`。
- 原始代码保存在 `vendor/`，自建实验和适配入口放在外部。

## 最终实测结果

- 传统实验基频 144.282791 Hz，刚度乘 4 后 288.565582 Hz，质量乘 4 后 72.141396 Hz。
- 最大特征对相对残差约 1.77e-13，独立物理坐标 DOP853 速度校验相对误差约 1.22e-10。
- 阻尼乘 4 时第一模态振幅 T60 从 3.317552 s 减为 0.829388 s；该指标不是房间混响时间。
- 五段 WAV 为 48 kHz、PCM16、3 s，共用播放增益，无 NaN、无削波，回读检查通过。
- 官方体素梁：24 个六面体，63 节点，189 个原始自由度，固定端后 162 个自由度，质量 0.20544 kg。
- 官方 FEM 首阶频率 529.322546 Hz；特征对残差约 1.27e-13，与稠密求解最大相对特征值误差约 1.48e-12。
- 自由体六个刚体零模态、约束后正谱、Young 模量/密度/尺寸缩放检查均通过。
- 三张结果图已作视觉检查；没有主观听音评测结论。
- 最终环境 `python -m pip check` 返回 `No broken requirements found.`。

证据：`traditional/outputs/metrics.json`、`neuralsound/outputs/metrics.json`、两处 `RESULTS.zh-CN.md`、`logs/traditional-run.log`、`logs/official-fem-run.log`。

## 环境与运行

- Conda 程序：`C:/ProgramData/anaconda3/Scripts/conda.exe`。
- 新环境：`F:/System/Desktop/3DGS/复现/.conda/acoustics`。
- Python 3.11.18；NumPy 1.24.3；SciPy 1.10.1；Matplotlib 3.10.9；Numba 0.68.0。
- 精确 Windows 包清单：`conda-explicit-win64.txt`；环境导出：`environment.yml`；直接依赖：`requirements-direct.txt`。
- 安装日志：`logs/conda-create.log`、`logs/conda-numba.log`。未修改其他 Conda 环境或系统驱动。
- 从工作目录执行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\reproduction\run.ps1` 可重复运行；添加 `-SkipOfficial` 只运行传统声音实验。同名结果和日志会被覆盖。

## 输入、来源与修改

两个上游仓库跟踪文件均未修改。官方实际调用源文件 SHA256 在 `neuralsound/outputs/metrics.json`。
`traditional/` 是本地自建简化实验；`neuralsound/run_official_fem.py` 是新增包装器，生成输入体素梁、约束边界并做校验，不冒充作者原始入口。没有预训练权重输入。

## 下一步

先使用现有音频、三张图和 `MEETING_NOTES.zh-CN.md` 整理组会。继续完整复现前，先取得匹配的 NeuralSound 权重与推理配置，或补齐 PAT 声辐射求解与样例链；之后再推进 GPU 和 3DGS 联动。
