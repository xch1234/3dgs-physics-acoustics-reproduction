# Ficus 原始图像重建训练

真实执行上游 3DGS train.py 30,000 步、render.py 和原 SSIM/PSNR/LPIPS 指标函数。800×800、白背景，100 train / 200 test，`--eval`；val 100 张也已下载但未用于测试指标。输入来自固定 revision 的公开 NeRF synthetic 镜像；镜像出处及每文件哈希见 [数据来源](ficus-dataset-provenance.json)。这不等于已核实作者 Drive 压缩包逐字节相同。

测试平均 PSNR 34.847324 dB、SSIM 0.987181、LPIPS-VGG 0.011694。模型训练使用原优化参数，图像放 CPU 节约显存；评估逐图读取，保留原指标实现。LPIPS/VGG 权重来源有单独哈希记录。

- [四组测试视图对照](../outputs/ficus_reconstruction/heldout_comparison.jpg)
- [完整训练与评估指标](reconstruction-metrics.json)
- [逐图结果](../outputs/ficus_reconstruction/evaluation.json)
- 模型：`outputs/ficus_reconstruction/point_cloud/iteration_30000/point_cloud.ply`
- 训练/渲染/指标日志：`logs/ficus-reconstruction-*.log`

执行 `./run_reconstruction.ps1`；断点和阶段参数见同名 code 脚本。作者发布的 PhysGaussian Ficus `cfg_args` 使用 eval=False，不能用它声称独立测试泛化；本次新训练严格区分测试集。单一 Ficus 的指标也不是全部 3DGS 或 PhysGaussian 论文基准复现。

## 重新接入物理模拟

已将本次独立训练的最终 PLY 用于相同 Ficus 配置的完整五秒模拟及 125 帧 SH 渲染。入口 `run_reconstructed_simulation.ps1`；[视频](../outputs/ficus_reconstructed_full/output.mp4)、[运行指标与模型哈希](../outputs/ficus_reconstructed_full/metrics.json)。与作者发布模型的结果分别保存。
