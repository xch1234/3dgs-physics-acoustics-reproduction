# 全部独立测试预测

[全部24张图概览](../outputs/radiation_training/all_test_predictions/overview.jpg)

保留第86轮验证集选定的冻结权重，对24张独立测试图保存完整参考与原始预测数组。未调参或重新选择权重；重新计算误差与首次测试逐项一致。
图中每一对参考/预测使用相同物理FFAT色标，幅值偏差不通过单独归一化隐藏；与训练报告中的归一化方向图含义不同。

[完整数组](../outputs/radiation_training/all_test_predictions/predictions.npz) · [权重哈希与检查记录](../outputs/radiation_training/all_test_predictions/export-metrics.json)

- [样本 1–4](../outputs/radiation_training/all_test_predictions/test_00_03.png)
- [样本 5–8](../outputs/radiation_training/all_test_predictions/test_04_07.png)
- [样本 9–12](../outputs/radiation_training/all_test_predictions/test_08_11.png)
- [样本 13–16](../outputs/radiation_training/all_test_predictions/test_12_15.png)
- [样本 17–20](../outputs/radiation_training/all_test_predictions/test_16_19.png)
- [样本 21–24](../outputs/radiation_training/all_test_predictions/test_20_23.png)
