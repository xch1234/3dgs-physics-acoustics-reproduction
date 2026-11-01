# 训练网络到音频的本地完整链路

对象在训练前固定为独立测试集 box_21。输入来自实际训练后 defaultUnet 初始化加 LOBPCG 精修，不是用稠密参考模态替代网络流程；随后调用实际训练的 AcousticNet 权重，输出六张远场幅值 FFAT 并合成三个听者的声压 WAV。

材料为受控的 0.01 倍 Ceramic 刚度：E=7.2e8 Pa、ρ=2700、ν=0.19；不是测量真实陶瓷。频率为 1572.64, 1918.53, 2329.35, 3723.11, 3935.87, 4225.72 Hz。模态先做物理质量归一化；最大残差 1.09e-08。原 Bempp 双精度算子作为相同输入参考，六次 GMRES 均检查返回码与真实残差。

逐模态 FFAT 相对 L2：50.51%, 60.25%, 56.93%, 55.09%, 64.28%, 73.03%。原始负预测比例 0.000%；仅在音频合成时将负幅值截至零，FFAT 误差按未截断预测报告。三位听者音频相对 L2：263.63%, 136.37%, 98.29%。

1e-4 N·s 固定方向冲量，距离 0.3 m，Rayleigh α=6、β=1e-7；48 kHz / 3 秒 / PCM16。参考与网络音频共用同一播放增益，原始 Pa 数据和增益另存 raw.npz。末端仅加 20 ms 淡出。

- [波形与 FFAT 图](../outputs/neural_audio/neural_audio.png)
- [全部数值与权重哈希](neural-audio-metrics.json)
- 听者 1：[BEM](../outputs/neural_audio/bem_listener_1.wav) / [神经](../outputs/neural_audio/neural_listener_1.wav)
- 听者 2：[BEM](../outputs/neural_audio/bem_listener_2.wav) / [神经](../outputs/neural_audio/neural_listener_2.wav)
- 听者 3：[BEM](../outputs/neural_audio/bem_listener_3.wav) / [神经](../outputs/neural_audio/neural_listener_3.wav)

这里完成的是本地受控链路，不是论文全数据集精度。采用幅值近似，没有相位、传播延迟、Doppler、接触力求解或碰撞引擎；也没有主观听感评价。运行命令 `./run_numerical.ps1 -Task audio`，需先生成两个已训练网络和混合模态产物。
