# PhysGaussian 可选各向异性正则实验

按预先固定的 [协议](ANISOTROPY_PROTOCOL.md) 实现式(12)，r=5、λ=0.01；单独从头执行完整30,000步训练、200测试视图、原5秒/125帧模拟。上游文件未改，外部AST只在图像损失赋值处加入正则项；保存源文件哈希、适配行号与逐千步诊断。此为本地Ficus方法验证，不是原图8凳子及未公开参数的复现。

- 未正则化：294,804 个高斯；平均轴比 13248.2，中位 4412.18，95分位 53422.2，超过5的比例 99.063%。PSNR 34.847324 dB、SSIM 0.987181、LPIPS 0.011694。
- 正则化：309,479 个高斯；平均轴比 4.47941，中位 4.58496，95分位 4.96979，超过5的比例 0.617%。PSNR 34.280759 dB、SSIM 0.985905、LPIPS 0.012802。

正则项是软惩罚，不要求最大轴比严格≤5。密化与优化耦合使最终粒子数可变化；均值降低本身不证明动态视觉或物理质量提高。保持原测试集，不按这些结果重新选阈值、权重或检查点。梯度有限差分、已知值、尺度不变性检查见 [函数验收](anisotropy-function-check.json)。

首次模拟启动遇到旧Warp生成源码的ASCII编码错误，随后导入修复又暴露同名模块/命名空间包冲突；两次失败日志分别保存为 [编码失败](../logs/ficus-anisotropy-simulation-first-ascii-failure.log) 和 [导入失败](../logs/ficus-anisotropy-simulation-import-failure.log)。外部适配器先建立命名空间包，再优先从既有ASCII别名导入MPM叶模块。未修改上游或项目外文件。恢复时只执行模拟，保留已完成的训练、200视图渲染和评估；metrics中的计时仅对应恢复调用，未反推或虚构之前各阶段用时。[原训练参数](../outputs/ficus_anisotropy/adapter-protocol.json)。

[全部指标和实际命令](anisotropy-metrics.json) · [轴比分布](../outputs/ficus_anisotropy/axis_ratios.png) · [测试图](../outputs/ficus_anisotropy/heldout_comparison.jpg) · [完整视频](../outputs/ficus_anisotropy_full/output.mp4) · [逐帧状态](../outputs/ficus_anisotropy_full/metrics.json)。训练模型哈希与模拟输入一致。
