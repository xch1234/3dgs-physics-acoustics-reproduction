# NeuralSound 复现记录

日期：2026-11-01（Asia/Shanghai）。**当前完成官方传统 FEM 数值模块，尚未完成 NeuralSound 神经网络或端到端论文复现。**

## 论文与代码

论文在 `../paper/NeuralSound_2022.pdf`。官方项目 <https://hellojxt.github.io/NeuralSound/>，仓库 <https://github.com/hellojxt/NeuralSound>，当前 main/HEAD 为 `b18e81b1e3dba7e963b09a7d9a45b584707d805f`；11 月 1 日通过 `git ls-remote` 再次核实，见 `remote-refs.txt`。

本地作者代码位于 `../code/NeuralSound`，跟踪文件未修改。包装器 `../code/run_official_fem.py` 是本地代码，提供输入、边界条件、参考求解与验证；作者的矩阵组装、模型类及 Lanczos 函数按原样调用。

## 已运行的内容

6×6×6 体素网格内的 24 单元塑料梁；尺寸 0.12×0.04×0.04 m，固定 x 最小端面。求前 12 阶模态，检查总质量、矩阵对称性、质量正交、特征残差、自由体六个刚体模态、稠密求解参考，以及 Young 模量、密度和尺寸缩放关系。

这不是网络预测模态再做 Rayleigh–Ritz / LOBPCG 精修的混合算法。没有把 CPU Lanczos 的成功写成神经网络成功。

## 权重和入口重新核查

- 2026-11-01：项目页、GitHub Releases 页面和 issues 页面重新抓取为本目录 HTML；Releases 页面明确显示 “There aren’t any releases here”。
- 当前仓库跟踪文件仍无 `.pt` / `.pth` / `.ckpt` 权重。README 中 `weights/default_tag.pt` 为训练输出路径，不是预训练下载链接。
- 项目页仍链接论文、视频和代码，没有找到匹配预训练权重链接。未能发现可直接运行的预训练输入、权重、归一化和推理入口组合。
- GitHub API 本次触发未认证 rate limit，`github-*.json` 只记录请求失败，不能视作成功获取的空资源列表。保留上一轮有日期的 API 快照于 `previous_audit/`；本轮使用 HTML 和 git 远程引用补充核查。
- 网络搜索工具本轮返回错误，没有把检索失败作为“不存在权重”的证据。
- 已有网络定义和训练脚本；`dataset/mesh/example.obj` 存在，但从 mesh 到 voxel、FEM、FFAT 的官方数据生成链涉及额外 GPU/OpenCL 依赖。

因此准确结论为：**在已核查公开资源中未找到可下载匹配权重；尚不能运行有意义的预训练推理**，并非证明任何地方都没有权重。

## 官方完整环境与本次环境

官方 `environment.md` 为 Ubuntu 20.04、Python 3.7、CUDA 11.1，依赖 PyTorch、MinkowskiEngine、torch-scatter、PyCUDA、Bempp-cl 等。本次没有安装完整神经环境，没有用随机权重或玩具网络冒充论文结果。

本次运行使用项目根目录 `.conda/acoustics`：Python 3.11.18、NumPy 1.24.3、SciPy 1.10.1、Numba 0.68.0、Matplotlib 3.10.9；数值库线程数 1。`environment.yml` 和 `conda-explicit-win64.txt` 保存可恢复版本。

## 重复执行与证据

在项目根目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\03_NeuralSound\run.ps1
```

结果在 `../outputs/official_fem`，日志 `../logs/official-fem.log`。中文实测结果见 `RESULTS.md`；`metrics.json` 给出实际误差、输入和源码 SHA256。`../outputs/previous_fem` 是上轮结果，当前以 official_fem 为准。

本轮将输入 FEM 结果复制到 PAT 的 `inputs/official_fem_result.npz` 作为已知来源的小梁基线。这种共享只用于 PAT 声辐射实验，不表示已把两篇神经/传统论文完整结合。

## 未完成项及推进条件

1. 获得与公开架构匹配的预训练权重和推理配置，或另行安排完整训练数据生成、训练与验证；当前没有训练产物。
2. 在独立 Linux Conda 环境解决完整依赖，再进行 batch size 1、关闭梯度的单样本推理和显存测试。
3. 与数值参考比较频率、子空间和 FFAT 指标；近重根模态不能逐元素相减。
4. 连接外力与音频合成后才算端到端；运行 FFAT 图不等于生成声音。
5. 最后按论文数据划分、指标与硬件进行结果复现。当前 4GB 显存没有被证明能容纳完整网络。

以上是当前实际边界，不能写成“三篇论文全部完整复现”。
