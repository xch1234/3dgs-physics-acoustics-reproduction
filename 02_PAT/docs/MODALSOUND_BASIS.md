# ModalSound 官方 C++ 基函数运行

已编译并调用未修改的 `ModalSound/src/transfer/HelmholtzBasis.hpp`，使用独立 Conda GSL 2.7 与系统 GCC。此为 SIGGRAPH 2016 教学仓库的数值模块，不是 PAT 2006 原应用，也未假装已编译完整 Qt 图形界面或取得 FastBEM 输入链。

24 个空间点/波数，l=0…5，共 864 个奇异球基函数值，与独立 SciPy 参考相对 L2 误差 4.44e-16；解析方向导数与中心有限差分相对 L2 误差 6.5e-11。

重要约定：该代码使用第一类球 Hankel，正 m 球谐比 SciPy 多一个 (-1)^m 因子，负 m 与 SciPy 相同。本项目 PAT 自建实现使用第二类 Hankel 及 SciPy 球谐，二者不能直接混用系数。比较时已显式转换约定。

重跑：先在 WSL 执行 `code/run_modalsound_basis.sh`，再在 acoustics Conda 执行 `python 02_PAT/code/check_modalsound_basis.py`。

- [实际数值指标](modalsound-basis-metrics.json)
- [C++ 输出](../outputs/modalsound_basis/basis.txt)
