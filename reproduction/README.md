# 传统声学与 NeuralSound 小规模复现

> 这是 2026-10-31 基础阶段的归档说明，保留原始实验及结论。当前三个论文目录、完整场景、神经训练和声辐射结果请看 [复现总报告](../复现总报告.md) 和 [当前状态](../STATUS.md)；下文“尚未安装/未训练”等不代表最终状态。

本项目交付两条可复查的 CPU 路线：自建模态振动可听化，以及 NeuralSound 官方传统有限元模块。完成状态见 [STATUS.md](STATUS.md)。不把这些结果称为 PAT 完整复现或 NeuralSound 神经网络推理。

## 查看结果

- [传统实验中文结果](traditional/outputs/RESULTS.zh-CN.md)
- [物理趋势与独立校验图](traditional/outputs/physical_checks.png)
- [五组波形与频谱](traditional/outputs/waveforms_spectra.png)
- [按顺序试听五组音频](traditional/outputs/comparison_all.wav)
- [官方 FEM 中文结果](neuralsound/outputs/RESULTS.zh-CN.md)
- [官方 FEM 输入与频率图](neuralsound/outputs/official_fem.png)
- [官方代码可行性核查与阻塞项](audit/FEASIBILITY.zh-CN.md)

## 重复执行

从工作目录 `F:\System\Desktop\3DGS\复现` 执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\reproduction\run.ps1
```

仅运行传统声音实验：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\reproduction\run.ps1 -SkipOfficial
```

脚本使用 `.conda/acoustics/python.exe`，统一设置数值库单线程。输出写入各自 `outputs/`，日志写入 `logs/`；重复执行覆盖同名结果。Numba 首次运行需要编译，首次耗时不能当作稳定推理速度。

## Conda 环境

环境前缀：`F:\System\Desktop\3DGS\复现\.conda\acoustics`。

激活后可手动运行 Python：

```powershell
conda activate 'F:\System\Desktop\3DGS\复现\.conda\acoustics'
python .\reproduction\traditional\run_experiment.py
python .\reproduction\neuralsound\run_official_fem.py
```

安装完成后保存的 `conda-explicit-win64.txt` 用于在另一个新前缀恢复同版本 Windows 环境：

```powershell
conda create --prefix '<新的环境目录>' --file .\reproduction\conda-explicit-win64.txt -y
```

`environment.yml` 为实际环境导出，`requirements-direct.txt` 记录直接依赖版本。上游完整神经网络环境尚未安装；当前 Python 3.11 CPU 环境不等价于作者 Python 3.7/CUDA 环境。

## 代码来源和复现边界

- `traditional/run_experiment.py`：本地新写的质量弹簧模型、精确模态响应、对照、验证与绘图。
- `neuralsound/run_official_fem.py`：本地包装器，调用未修改的官方 FEM 组装和 Lanczos 求解代码；额外生成输入、施加固定边界、做稠密参考与尺度检查。
- `vendor/ModalSound`、`vendor/NeuralSound`：原始克隆，提交号与许可证记录在核查报告中；本次不修改上游跟踪文件。
- `traditional/outputs/*_raw.npz` 保留物理幅值。音频只是振动速度的可听化，未计算声辐射、声压级或听者方向性。
- 所有实验为小规模验证，未跑论文数据集或论文性能/精度基准，未与 3DGS 联动。

## 数值与文件检查

运行入口内包含必要断言：特征残差、质量正交、解析频率关系、独立 ODE 对照、能量衰减、音频有限值和回读无削波。
官方 FEM 另外检查总质量、六个自由体刚体模态、约束后正定谱、Lanczos 与稠密求解一致性、材料和几何尺度关系。
详情保存在各自 `outputs/metrics.json`，而不是只依赖终端的“成功”提示。
