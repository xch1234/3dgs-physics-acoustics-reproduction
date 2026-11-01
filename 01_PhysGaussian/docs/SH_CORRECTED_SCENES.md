# 非单位预旋转场景的完整 SH 坐标修复验证

在原模型、原完整配置和原物理求解器上，仅通过外部适配器将MPM逆旋转变换至世界坐标。原发布版结果保持。每帧在完全同一粒子状态、相机和光栅参数下另外渲染未修正颜色，避免把两次物理模拟差异误判为SH修复效果。
逐帧差异由光栅器的浮点RGB输出计算；四个选定帧额外保存完整原始浮点图像对，并独立复算L2/平均绝对差/最大绝对差。PNG/MP4是量化后的观看版本，不能要求从8位图像逐比特重建这些浮点误差。

## bread

300帧；同状态修复前后图像相对L2均值 0.00601977，最大 0.0108672。此数值是两种算法之差，不是相对真实图像的误差或修复收益。
[完整视频](../outputs/bread_sh_corrected/output.mp4) · [同状态对照](../outputs/bread_sh_corrected/same_state_comparison/overview.jpg) · [首个浮点图像对](../outputs/bread_sh_corrected/same_state_comparison/frame_0001_raw.npz) · [指标](../outputs/bread_sh_corrected/metrics.json)

## plane

400帧；同状态修复前后图像相对L2均值 0.012695，最大 0.0177852。此数值是两种算法之差，不是相对真实图像的误差或修复收益。
[完整视频](../outputs/plane_sh_corrected/output.mp4) · [同状态对照](../outputs/plane_sh_corrected/same_state_comparison/overview.jpg) · [首个浮点图像对](../outputs/plane_sh_corrected/same_state_comparison/frame_0001_raw.npz) · [指标](../outputs/plane_sh_corrected/metrics.json)

## vasedeck

75帧；同状态修复前后图像相对L2均值 0.0329425，最大 0.0831046。此数值是两种算法之差，不是相对真实图像的误差或修复收益。
[完整视频](../outputs/vasedeck_sh_corrected/output.mp4) · [同状态对照](../outputs/vasedeck_sh_corrected/same_state_comparison/overview.jpg) · [首个浮点图像对](../outputs/vasedeck_sh_corrected/same_state_comparison/frame_0001_raw.npz) · [指标](../outputs/vasedeck_sh_corrected/metrics.json)

公式正确性由 [独立不变量实验](SH_FRAME_AUDIT.md) 验证。完整场景测试证明适配器实际接入原渲染链且输出有效，缺少动态真实图像时不宣称视觉指标提升。未重跑Q为单位阵的Ficus/Wolf以及默认无旋转的Pillow，因为该转换在这些情况下恒等。
