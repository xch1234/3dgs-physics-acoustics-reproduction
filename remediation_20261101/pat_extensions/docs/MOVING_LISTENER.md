# PAT 移动听者与运行时求值

使用已保存的 12 模态、1792 面片 BEM 密度及多极子系数，不重新拟合。听者在半径 0.25 m 的环形路径运动，高度同时变化；每 0.5 秒施加相同的 0.001 N·s 模态冲量，持续 3 秒。传递函数以 200 Hz 更新并插值至 48 kHz 音频。

复声压传递相对误差 0.787%，合成声压音频相对误差 0.229%。BEM 与 PAT 使用同一个播放增益，保留未经归一化的 Pa 波形。遵循论文的幅值传递近似，未包含多普勒、传播延迟或接触碰撞求解。

- [PAT 移动听者音频](../outputs/moving_listener/pat_moving.wav)
- [BEM 对照音频](../outputs/moving_listener/bem_moving.wav)
- [路径、波形和运行时间图](../outputs/moving_listener/moving_receiver.png)
- [完整参数与计时](moving-listener-metrics.json)

对 1、8、64、256 个听者分别预热后计时三次，保存所有时间与中位数。两种方法均复用预计算，BEM 测量的是边界密度到外场的求值。此为本地 Python 实现且可能受后台任务影响，不能宣称复现论文的 7000 倍性能。

重跑：在项目 acoustics Conda 中运行 `python 02_PAT/code/run_moving_listener.py`，先确保扩展实验已生成全部 mode NPZ。
