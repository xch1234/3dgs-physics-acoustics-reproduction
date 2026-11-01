> 发布说明：下文为历史实验记录。当前验收结论以 [独立验证报告](../verification_20261101/独立验证报告.md) 为准；不能据此认定三篇论文完整复现成功。大文件由 Releases 按原路径恢复。

# NeuralSound

已实际从零训练公开 defaultUnet 与 AcousticNet，完成本地独立几何测试及六阶模态到声压 WAV 的链路。使用小规模程序化数据，不等同于论文 ABC 数据精度。

- [复现记录](docs/REPRODUCTION.md)
- [实际训练和测试](docs/TRAINING_RESULTS.md)
- [神经音频及 BEM 对照](docs/NEURAL_AUDIO.md)
- [官方网格体素化与模态求解](docs/OFFICIAL_EXAMPLE.md)
- [BEM 标签核查](docs/BEM_CROSSCHECK.md)

训练入口 `run_neural.ps1 -Task vibration|radiation`，数值/音频入口 `run_numerical.ps1 -Task example|bem|labels|audio`，基础 FEM 为 `run.ps1`。详见根目录 [环境与复跑](../复跑与环境说明.md)。

## 补充实验

- [包含网络初始化成本的三次重复计时](docs/VIBRATION_BENCHMARK.md)
- [作者原始网格的神经振动混合求解](docs/EXAMPLE_HYBRID_OOD.md)
- [保留原失败结果的更长迭代收敛诊断](docs/EXAMPLE_HYBRID_OOD_EXTENDED.md)
- [作者原始网格的冻结声辐射网络测试](docs/EXAMPLE_ACOUSTIC_OOD.md)
- [CPU Adam 存储、数值一致性与性能记录](docs/CPU_ADAM_PROFILE.md)
- [声辐射预测未达标：平均、中位数及逐物体误差](docs/RADIATION_ACCURACY.md)
- [全部24张测试图：物理幅值对照与原始数组](docs/ALL_TEST_PREDICTIONS.md)
- [本地特征编码与作者数据类的 12 样本对照](docs/acoustic-feature-contract.json)
- [四个训练检查点实际读回与恢复状态验收](docs/checkpoint-audit.json)
- [保存的12组振动模态重新装配物理FEM复核](docs/vibration-array-audit.json)

[正文优化器参数对照结果](docs/PAPER_SCHEDULE_RESULTS.md)：两网络另训100轮、全部预测与检查点验收；不覆盖或替代原发布参数实验。
