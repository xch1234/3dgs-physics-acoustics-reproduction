# 官方网格的声辐射泛化检查

在完成网络训练前固定测试作者 example.obj 的前两个 Ceramic 模态（2877.47, 3021.66 Hz），其频率位于本地增强范围，但几何不属于训练长方体族。3863 体素、8144 表面三角面；官方 Bempp 双精度/Numba 算子生成独立参考并检查显式残差。首次 GMRES 500 次后残差 2.35e-5，未达标；失败日志保留。最终参考允许在 GMRES 失败时对同一组装矩阵使用 SciPy 直接 LU，不放宽 1e-8 容差；实际方法和两次原始 GMRES 结果记录在指标中。对应矩阵、右端项、失败迭代系数和直接解均保存。

冻结已训练公开 AcousticNet，未用此物体选择权重或调参。两张 FFAT 的平均相对 L2 为 **99.806%**。这项指标直接反映局部简单数据的泛化局限，不以能生成预测图代替精度达标。

本次推理设备为 `cuda:0`。曾尝试 CPU，但 MinkowskiEngine 的全局池化在此输入触发 `Invalid out_coordinate_map` 断言，失败日志为 `logs/example-radiation-ood-cpu.log`；不能把 CPU 尝试称为成功。本次 CUDA 推理前实测空闲显存约 2519 MiB，而已运行同网络单样本推理峰值约 1.26 GB，因此与较低显存的 Wolf 模拟并行调度；不使用此次墙钟宣称推理速度。

[指标与参考审计](example-acoustic-ood-metrics.json) · [真实参考/预测图](../outputs/example_acoustic_ood/maps.png)。参考保存在 inputs/official_example_acoustic。本测试使用独立 FEM 模态以单独评估声辐射，并非此网格上的神经振动端到端结果。

先在 Linux NeuralSound Conda 运行 `python code/run_example_acoustics.py --prepare`，然后使用 CUDA 运行 `--predict`。保留的 `--device cpu` 仅用于重现上述失败，不是此输入的可用替代入口。大网格 BEM 与训练同时运行可能超过内存；参考 elapsed_s 包含约 1.5 分钟为独立计时而暂停的调度，不能当论文性能。
