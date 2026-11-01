# 本轮作者网格的声辐射泛化检查

实际体素数 3863；固定前两个 Ceramic 模态的频率为 2877.472 Hz、3021.665 Hz。

使用本轮独立 FEM 参考与原 Bempp 双精度算子。若 GMRES 未达标，在同一组装方程上使用直接 LU；不放宽残差要求。每次实际求解记录如下：

- {"method": "SciPy dense LU on identical Bempp weak form", "info": 0, "relative_residual": 5.115959454462984e-15, "gmres_attempt": {"info": 500, "relative_residual": 2.353225296742328e-05, "iterations": 500}}
- {"method": "SciPy dense LU on identical Bempp weak form", "info": 0, "relative_residual": 6.1125989494187414e-15, "gmres_attempt": {"info": 500, "relative_residual": 7.733406294640421e-07, "iterations": 500}}

冻结本轮 released_profile 模型，CUDA 推理两张图的平均原始相对 L2 为 99.8048%。没有为此物体选权重或调参。

本轮 GPU 重任务串行执行；没有与狼场景并行，也没有人为暂停这次 BEM 计时。此处未重跑 CPU 推理，旧文档中的 CPU 全局池化失败属于历史记录；不将其写成本轮新测试。

[实际指标及参考残差](example-acoustic-ood-metrics.json) · [参考/预测图](../outputs/example_acoustic_ood/maps.png)。这是两模态的局部泛化检查，不是完整 ABC 基准，也不是该网格的神经振动到声辐射端到端系统。
