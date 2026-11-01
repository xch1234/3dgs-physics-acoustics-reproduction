# 公开神经网络实际训练结果

生成时间：2026-11-01T12:15+08:00。采用 [预先记录的本地协议](LOCAL_TRAINING_PROTOCOL.md)，原网络源码不修改。实际权重、每轮损失和测试产物位于 `outputs/vibration_training` 与 `outputs/radiation_training`。

## 振动与混合求解

defaultUnet(24,48,linear=True)，200 轮。初始验证 loss 1.1058963，最佳验证 loss 0.15997582；验证改善标记 True。图矩阵乘法与组装 FEM 的 K/M 相对误差分别为 9.18e-08 / 8.04e-08。测试物体比较随机、未训练网络、已训练网络三种初始化，随后均使用公开 LOBPCG 双精度精修。完整误差、迭代轨迹和单次用时见 [指标](vibration-training-metrics.json)，[学习曲线](../outputs/vibration_training/learning_curve.png)。

训练是单精度原始损失；严格最终求解采用双精度、最多 2000 步和 1e-10 内部容差。没有把数值精修后的准确性全部归因于网络，也没有从一次小实验推断论文加速。重根不逐元素比较特征向量。

## 声辐射

完整公开 AcousticNet(23)，311,180,810 个参数，优化器 cpu_adam，batch 40，100 轮。96/24/24 张 train/val/test FFAT，按几何划分。作者代码中 EncoderSmall 实际也构造 ResNet34，保持该结构。

初始验证 loss 4.0106934，最佳 0.36817554，改善标记 True。测试平均幅值恢复后 FFAT 相对 L2 为 **372.900%**。测试图、归一化图形误差、幅值对数误差和逐样本传递误差都保留：[指标](radiation-training-metrics.json)、[曲线](../outputs/radiation_training/learning_curve.png)、[测试图](../outputs/radiation_training/test_maps.png)。

CPU Adam 若启用，只把优化器状态和更新移至 CPU，保持公开网络及公式；12 步与 torch Adam 的数值对照结果记录在指标内。checkpoint 包含优化器、调度器、随机状态；不能承诺稀疏 GPU 操作跨机器逐比特一致。

## 不能据此宣称的结果

训练完成不等于达到论文精度。24 个简单长方体远小于 ABC 数据，物体数和频率分布都有限；最佳模型只由验证集选择，测试误差如实保留。没有公开匹配预训练权重的查找记录见 [基线审计](BASELINE_REPRODUCTION.md)，没有证明权重在任何地方都不存在。原始数据生成的单精度失败及标签改动见 [BEM 核查](BEM_CROSSCHECK.md)。

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
