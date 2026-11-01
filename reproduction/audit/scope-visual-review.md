# 本轮扩展实验视觉检查记录

2026-11-01，Asia/Shanghai。以下图片均在本轮实际打开检查；此前已完成的原始实验视觉记录保留在根目录执行记录中。图像检查用于发现空白、错位、布局和明显预测问题，不能替代完整数组验收或真实实验测量。

## PhysGaussian 各向异性实验

- [完整模拟四帧预览](../../01_PhysGaussian/outputs/ficus_anisotropy_full/contact_sheet.jpg)：实际检查第1、42、83、125帧，并另外打开原尺寸首尾PNG。植株和花盆主体可辨，未见空白或图像文件损坏；枝叶姿态随帧变化。相机变化与物理运动均可能影响外观，不从四帧估计物理精度。
- [轴比CDF](../../01_PhysGaussian/outputs/ficus_anisotropy/axis_ratios.png)：对数横轴、两曲线与阈值5的虚线清晰。正则化分布集中在约5附近，原基线有很长的高轴比尾部。该项为软惩罚，仍有超过5的高斯；轴比降低不等于动态视觉质量提高。
- [独立测试图对照](../../01_PhysGaussian/outputs/ficus_anisotropy/heldout_comparison.jpg) 已在训练评估完成后检查。正式结论使用全部200个测试视图的保存指标，而非挑选的缩略图。

## 三个SH坐标修复场景

各页上排为同一帧的原算法渲染，下排为坐标修复渲染；相机与物理状态相同，原始浮点图像对另存NPZ。

- [Bread四组图像对](../../01_PhysGaussian/outputs/bread_sh_corrected/same_state_comparison/overview.jpg)：第1、100、200、300帧。面包出现拉伸和分离，末帧右侧块体部分离开原相机画幅；原版和修复版均保留这一现象，没有重新裁切或改变相机掩盖它。两排几何对应，局部颜色有差别。
- [Plane四组图像对](../../01_PhysGaussian/outputs/plane_sh_corrected/same_state_comparison/overview.jpg)：第1、134、267、400帧。另打开第267帧两张原尺寸PNG。飞机、螺旋桨与背景可辨，几何位置对应，局部颜色有差别；不是动态真实图像的误差对照。
- [VaseDeck四组图像对](../../01_PhysGaussian/outputs/vasedeck_sh_corrected/same_state_comparison/overview.jpg)：第1、25、50、75帧。花朵、花瓶与木板背景可辨，上下两排的相机和物体构型对应，细节色彩存在差异。

没有根据这些图像宣称修复提高了动态PSNR或真实物理准确性。公式正确性由独立不变量实验验证，全部帧的有限性、质量和图像差异由数值验收检查。

## NeuralSound全部新测试预测

实际逐页打开六页，每页四组BEM/预测，共24组；每对采用相同物理幅值色标，负值也在显示范围内：

- [样本1–4](../../03_NeuralSound/outputs/radiation_paper_schedule/all_test_predictions/test_00_03.png)
- [样本5–8](../../03_NeuralSound/outputs/radiation_paper_schedule/all_test_predictions/test_04_07.png)
- [样本9–12](../../03_NeuralSound/outputs/radiation_paper_schedule/all_test_predictions/test_08_11.png)
- [样本13–16](../../03_NeuralSound/outputs/radiation_paper_schedule/all_test_predictions/test_12_15.png)
- [样本17–20](../../03_NeuralSound/outputs/radiation_paper_schedule/all_test_predictions/test_16_19.png)
- [样本21–24](../../03_NeuralSound/outputs/radiation_paper_schedule/all_test_predictions/test_20_23.png)

[总览图](../../03_NeuralSound/outputs/radiation_paper_schedule/all_test_predictions/overview.jpg) 也已打开检查。单页标题和色条可读；总览用于定位，细节应看单页。预测普遍呈相似网格纹理，未呈现参考声场的平滑方向分布。部分强辐射模态明显低估，部分弱辐射模态高估。未对图像平滑、裁去负值或另选样本；原因不能单凭图像判定。

[两组优化器参数验证曲线](../../03_NeuralSound/outputs/radiation_paper_schedule/optimizer_comparison.png) 已打开检查：两网络分别绘制，振动原配置200轮、正文参数100轮的长度差异明确；辐射早期尖峰保留。验证损失下降不代表FFAT幅值或论文泛化精度达标，也不把多项参数同时改变归因于单一因素。两组新学习曲线及归一化预览此前也已检查。

WAV采用PCM及原始数值检查；本次没有进行主观试听、音质评测或用户实验。
