# 官方网格、体素化与模态求解

本实验实际执行作者 `dataset/mesh/example.obj`、原始 PyCUDA 体素化核、Hexahedron FEM 和默认 GPU LOBPCG。运行入口：`./run_numerical.ps1 -Task example`；重复数值求解可使用 `code/run_neural_linux.sh example --reuse-voxel`。使用独立 Linux Conda `neuralsound`，PyCUDA 固定 2022.2.2。

## 已完成结果

- 32³ 网格中 3,863 个占用体素；17,898 个自由度，刚度矩阵 1,105,416 个非零项。
- 原始 GPU LOBPCG 用时 5.24 秒，返回 20 个弹性模态；独立双精度稀疏 shift-invert 参考用时 8.44 秒。计时是本机单次运行且同时存在 CPU 编译，不能据此推断论文速度。
- 参考模态频率为 2,877.47–18,808.10 Hz，最大独立相对残差 2.14e-9。
- 原求解器特征值最大相对误差约 0.879%，但严格向量残差范围为 0.00883–0.679。因此频率图接近不代表模态向量达到高精度收敛，原默认结果不能作为已收敛的声学参考。

残差定义为 `||Ku − λMu|| / (||Ku|| + ||λMu||)`；排除六个自由刚体模态。参考解显式检查这六个零特征值和弹性模态残差。没有修改作者求解器默认容差来掩盖差异。

## 产物和限制

- [数值指标](official-example-metrics.json)
- [体素与频率图](../outputs/official_example/example_validation.png)
- `outputs/official_example/voxel.npy`、`stiffness.npz`、`mass.npz`、`official_modes.npz`、`reference_modes.npz`
- [实际日志](../logs/official-example-full.log)

这项结果属于官方传统数值模块，单独不构成神经网络推理。官方样例不等于论文 ABC 全集测试。PyCUDA 2026.1 在 Python 3.9 上出现类型注解导入错误，退至 2022.2.2 后实测通过；失败安装日志保留。
