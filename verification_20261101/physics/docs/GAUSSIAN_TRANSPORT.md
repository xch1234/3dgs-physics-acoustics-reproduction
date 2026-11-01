# 高斯协方差、旋转与增量输运独立验证

实际调用未修改的 compute_cov_from_F、compute_R_from_F、g2p 和 convert_SH，对应论文 §3.4–3.6、式(8)–(10)。96 组正定协方差与正行列式变形，独立检查高斯指数不变、体积行列式规律、SciPy 极分解和物体/相机同步旋转后的三阶 SH 颜色。全部通过；详细误差见 [指标](gaussian-transport-metrics.json)。

增量分支在给定仿射速度场下与矩阵指数精确解对照，时间步 0.01/0.005/0.0025 秒，终点 0.2 秒。误差减半比为 2.00127、2.00097，符合显式 Euler 一阶收敛。正定性只在此步长和速度场验证，不声称任意大时间步都保持正定。默认完整场景使用总变形梯度分支；本实验额外覆盖原代码的增量开关。

原代码 compute_R_from_F 保存的是极旋转的转置，供 SH 逆向旋转视线使用，不能把它当正向旋转误判。参考数组保存在 [NPZ](../outputs/gaussian_transport/reference_arrays.npz)。本实验不替代论文变形图像基准或缺失 snow 材料。

重跑：在已配置 Linux physgaussian Conda 中执行 code/validate_gaussian_transport.py；入口 code/run_transport_audit.sh。代码、缓存与输出均位于项目内，仅只读使用现有 ASCII 源码软链接。
