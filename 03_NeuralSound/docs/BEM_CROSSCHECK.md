# 作者 Bempp 声辐射交叉核查

2026-11-01。已实际调用未修改的 `src/classic/bem/ffat.py` 与 `bemModel.py`，输入为本地 box_00 的六阶模态、作者体素表面拓扑及 291–5828 Hz 增强频率。仍不是 ABC 数据或作者论文测试集。

## 环境与数值适配

Bempp-cl 0.2.4 使用了 NumPy 1.24 删除的 `np.bool` 等别名，外部脚本恢复其原本 builtin 类型含义。作者 `voxel2boundary` 产生整值浮点索引，包装器仅把索引转为整数。

POCL 1.3 / LLVM 8 在本机 i5-12500H 上首次发生 `Cannot select ... fsqrt`；指定 Haswell 和禁用向量化后仍出现段错误。两次日志保留。改用 Bempp 自带 Numba CPU 后端，保留原来的超奇异算子、伴随双层算子、DP0/P1 空间和外场积分。这是后端适配，不能比较原 OpenCL 性能。

## 实际发现

原始单精度算子与作者 `1e-10 * max(neumann_coeff)` 容差组合下，六次 GMRES 均返回 `info=500`。即使内部报告的残差很小，也不能把达到最大迭代次数称为收敛。原作者函数没有检查这个返回码，本轮把它显式记录。

另一次使用双精度算子和统一相对容差 1e-8，六次 GMRES 均 `info=0`，且重新计算 `||A x-b||/||b||` 确认满足阈值。此项精度/容差改动明确区别于原始配置。单精度和双精度的 FFAT 差异远小于本地 BEM 与 Bempp 的差异。

双精度 Bempp 与先前本地间接常面元 BEM 的六阶远场幅值图相对差异约为 10.93%、68.90%、5.22%、9.67%、0.99%、28.47%。这些不是网络误差；两种方法的离散空间、求解形式不同，弱辐射模式中相对误差尤其敏感。不能把早先本地 BEM 标签当作作者标签，也不能用 PAT 对本地 BEM 的小拟合误差掩盖声学离散误差。

因此后续辐射网络改用作者 Bempp 算子重新生成全体 24 个本地对象的 144 张标签。保留原 `inputs/procedural_training` 作为独立对照，新数据另存 `inputs/procedural_bempp`；只有全部显式残差检查通过后才用于训练。最终生成完成状态见该目录的 `dataset.json`，本文件本身不宣称全量已完成。

## 证据与重跑

- [原单精度实际指标](official_bem_numba-metrics.json)
- [双精度及显式残差指标](official_bem_practical_tolerance_numba_double-metrics.json)
- [双精度对照图](../outputs/official_bem_practical_tolerance_numba_double/map_comparison.png)
- 原始失败日志：`logs/official-bem-numpy-failure.log`、`official-bem-pocl-failure.log`、`official-bem-pocl-haswell-segfault.log`。
- 对照脚本：`code/validate_official_bem.py --backend numba --precision double --tolerance 1e-8`。
- 全量生成：在 Linux NeuralSound Conda 中运行 `python code/generate_official_labels.py`，支持按已有通过检查的样本续跑。

本次未声称 Bempp 已达到网格收敛或测量声压精度；它给出与所选官方离散算子一致、线性求解收敛可验证的数据。
