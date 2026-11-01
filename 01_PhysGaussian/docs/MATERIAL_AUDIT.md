# 官方材料核验证

2026-11-01。代码 `../code/validate_materials.py` 在 Windows Conda / Warp CUDA 上真实运行，调用未修改的官方 `compute_stress_from_F_trial`。这是材料点的指定变形测试，不是完整空间仿真或论文场景。

E=20 kPa、ν=0.3、屈服参数 200 Pa、foam 塑性黏度 100、plasticine 软化参数 600、sand 摩擦角 30°。指定简单剪切 γ 从 0 增至 0.8 再回到 0，逐步对上一步弹性变形施加相对总变形；321 个采样点，dt=0.002 s。

- Jelly FCR 应力与独立 NumPy 解析公式相对误差 7.04e-7。
- 对叠加刚体旋转的客观性检查，相对误差 2.22e-7；纯旋转残余应力范数约 0.00138 Pa。
- Sand 均匀拉伸应力范数约 0.038 Pa，与无黏聚颗粒不承受拉力的行为相符。
- Jelly 卸载后基本回到零；metal 和 foam 出现塑性/黏塑性滞回；plasticine 随累计塑性变化软化至零应力。低压纯剪切中的 sand 应力很小，不能将它解读为具有有限黏聚屈服强度。

**发现上游 snow 选项未实现应力分支。** 参数解析把 `snow` 设为材料编号 4，但应力核仅处理 0、1、2、3、5，编号 4 的应力变量始终保持初始零值。本次测试确认整条 snow 曲线严格为零。因此不能把该开关产生的运动称为雪材料复现；本轮没有添加自编雪模型冒充上游方法。

图：[stress_paths.png](../outputs/material_audit/stress_paths.png)。每种材料的原始应力、弹性变形梯度和屈服参数均保留于 `../outputs/material_audit/*.npz`；机器可读结果：[material-metrics.json](material-metrics.json)。plasticine 最终屈服参数可略小于零，这是上游实现的破坏开关行为，已按原样记录，没有修改源代码。
