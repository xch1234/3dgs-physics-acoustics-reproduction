# ModalSound 原始 C++ 四面体 FEM

实际编译和调用原 `DeformableFEM::mass_mat`、`stiffness_mat` 与 `StVKMaterial::stiffness_matrix`，未修改上游源码。外部 C++ 驱动提供网格和输出；独立 Python 参考使用线性四面体 BᵀDB 公式。

本地 0.12×0.04×0.04 m 梁，63 顶点、144 四面体，E=3.5 GPa、ν=0.35、ρ=1050。总质量 0.201600 kg；自由体检查六个刚体零模态，固定体固定 x 最小面 9 顶点。原 mass_mat 为单位密度矩阵，外部仅乘一次密度。

三组刚度参考最大相对误差 5.51e-16；质量最大相对误差 5.44e-16；模态最大残差 1.32e-12。固定梁首频 1002.744250 Hz，E 乘 4 后所有频率乘 2，比例最大误差 0。

[完整指标](modalsound-fem-metrics.json) · [频率图](../outputs/modalsound_fem/frequencies.png)。矩阵、模态、网格与实际编译二进制保存在 outputs/modalsound_fem。用 `code/run_modalsound_fem.sh` 重跑，Conda pat-tools 提供 Boost 头文件，GCC 9.4 编译，Python 科学计算使用 Linux physgaussian Conda。

这比仅运行球谐基函数进一步验证了真实作者工具中的 FEM；仍不是 PAT 2006 原始场景/测量基准或完整 Qt/FastBEM GUI。与现有 NeuralSound 六面体梁的频率差异不能直接解释为某个实现有错，两种网格的离散精度不同。未运行网格收敛研究。
