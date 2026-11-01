# 原 ModalSound 边界积分与多极子后处理

本次实际编译运行 BoundaryIntegralTransfer、FMMBoundIntTransfer::compute_moments/eval/store_moments。使用三个非对称复单极点声源的解析声压与梯度，生成明确标记的 FastBEM 格式测试输入。它们不是 FastBEM 求解器输出，也没有取得该外部求解器。未修改上游头文件。

80/320/1280 面片，400/1800/6000 Hz，每例 240 个独立外部查询点；保留原代码自选展开阶数、文本及二进制矩系数。边界法向指向物体内部（外部空气域的外法向）；采用 e^(-iωt)、第一类 Hankel，不能与本地 PAT 的相反相位约定直接混用。

- 400 Hz、80 面片：原积分/解析误差 0.0475783，多极子/原积分 1.08e-08。
- 1800 Hz、80 面片：原积分/解析误差 0.0475756，多极子/原积分 3.9e-09。
- 6000 Hz、80 面片：原积分/解析误差 0.0501612，多极子/原积分 3.29e-10。
- 400 Hz、320 面片：原积分/解析误差 0.0116277，多极子/原积分 2.95e-09。
- 1800 Hz、320 面片：原积分/解析误差 0.0116278，多极子/原积分 9.41e-10。
- 6000 Hz、320 面片：原积分/解析误差 0.0116942，多极子/原积分 6e-10。
- 400 Hz、1280 面片：原积分/解析误差 0.00289039，多极子/原积分 1.89e-10。
- 1800 Hz、1280 面片：原积分/解析误差 0.00289043，多极子/原积分 5.94e-11。
- 6000 Hz、1280 面片：原积分/解析误差 0.00290227，多极子/原积分 1.27e-11。

各频率的解析误差随加密下降，最细网格低于 3%；多极子求值与相同离散积分相符，独立 SciPy 对保存系数的复算也通过。这里只验证后处理，不把多极子与积分接近当作连续声场同等准确，更不是 PAT 2006 自适应 source placement 的原始实现。

[指标](modalsound-transfer-metrics.json) · [收敛图](../outputs/modalsound_transfer/convergence.png) · [参考数组](../outputs/modalsound_transfer/reference_arrays.npz)。重跑 code/run_modalsound_transfer.sh；使用已有 Conda GSL/Boost 与项目内固定 Eigen 3.3.7 头文件，下载来源和 SHA256 见 code/dependencies/eigen-provenance.json。没有安装 Qt、没有变更系统或项目外配置。
