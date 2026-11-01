# NeuralSound 当前复现记录

已实际运行公开 defaultUnet 与 AcousticNet 的本地训练、独立几何测试及模态到声压音频链路。原仓库提交 `b18e81b1e3dba7e963b09a7d9a45b584707d805f`，跟踪源码保持未修改。不能将本地 24 个长方体训练称为 ABC 全数据或作者预训练性能。

- [训练协议](LOCAL_TRAINING_PROTOCOL.md)、[实际训练与测试结果](TRAINING_RESULTS.md)
- [训练网络到音频](NEURAL_AUDIO.md)
- [作者网格 CUDA 体素化与 FEM/LOBPCG](OFFICIAL_EXAMPLE.md)
- [作者 Bempp 算子交叉核查](BEM_CROSSCHECK.md)、[144 张标签的求解审计](official-labels-dataset.json)
- [基础 FEM 数值验证](RESULTS.md)

实际环境是 WSL Ubuntu1 `/opt/3dgs-runtime/envs/neuralsound` 的独立 Conda，Python 3.9、PyTorch 2.0+cu118、CUDA 11.8、MinkowskiEngine、torch-scatter、Bempp-cl 0.2.4、PyCUDA 2022.2.2。MinkowskiEngine 源码提交 `02fc608bea4c0549b0a7b00ca1bf15dee4a0b228`，在 Linux 磁盘上单任务编译。NumPy 旧别名、整值索引转换、Numba CPU/双精度算子及 CPU Adam 等适配均明确记录，原训练网络不替换为玩具代理。

重跑见 [统一环境与命令](../../复跑与环境说明.md)，各个 run_neural/run_numerical 入口与 code 脚本保存实际参数。训练权重、最佳选择过程、测试误差、随机状态及源文件哈希均可查。早期权重资源核查和 Windows FEM 环境见 [归档记录](BASELINE_REPRODUCTION.md)；其中“尚未训练”只代表早期状态。

默认单精度传统求解存在真实精度问题，未删除失败证据；声辐射误差如实报告。未复现完整 ABC 泛化、论文速度、全刚体接触/碰撞系统，也未取得与公开架构匹配的作者预训练权重。

## 补充实验

- [包含网络初始化成本的三次重复计时](VIBRATION_BENCHMARK.md)
- [作者原始网格的神经振动混合求解](EXAMPLE_HYBRID_OOD.md)
- [保留原失败结果的更长迭代收敛诊断](EXAMPLE_HYBRID_OOD_EXTENDED.md)
- [作者原始网格的冻结声辐射网络测试](EXAMPLE_ACOUSTIC_OOD.md)
- [CPU Adam 存储、数值一致性与性能记录](CPU_ADAM_PROFILE.md)
- [声辐射预测未达标：平均、中位数及逐物体误差](RADIATION_ACCURACY.md)
- [全部24张测试图：物理幅值对照与原始数组](ALL_TEST_PREDICTIONS.md)
- [本地特征编码与作者数据类的 12 样本对照](acoustic-feature-contract.json)
- [四个训练检查点实际读回与恢复状态验收](checkpoint-audit.json)
- [保存的12组振动模态重新装配物理FEM复核](vibration-array-audit.json)

正式声辐射训练采用原 batch 40、CPU 线程 8；96 张训练图每轮随机打乱后 drop_last，每轮两批，使用 80 张。batch 2 是独立资源试验，未用于初始化正式权重。CPU master Adam 另有 18 次更新（含第 9 次保存恢复）的独立数值核对；正式训练内也执行短对照。随机数状态的实际调用顺序见训练协议。

[正文优化器参数对照结果](PAPER_SCHEDULE_RESULTS.md)：两网络另训100轮、全部预测与检查点验收；不覆盖或替代原发布参数实验。
