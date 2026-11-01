# PAT 扩展复现实测结果

2026-11-01，实际运行约 441 秒，日志 `../logs/pat-extended.log`。入口 `../run_extended.ps1`，代码 `../code/run_pat_extended.py`。

## 新增的论文方法

在前轮小梁基础上继续实现 §4.3.2：由长方体有符号距离场经 marching cubes 提取 0.02 m 偏移面，网格间距 0.005 m，共 4568 个面片重心采样，按面片面积加权。使用 l=0,1,2 的九项球面多极子；每轮重新生成 128 个内部候选中心，三个层级、α=1/4，按面积和平方加权残差各半的概率抽取粗层样本，逐级筛选后在全采样面上选择最优中心，再对所有已选源做阈值 1e-6 的 SVD 重拟合。

使用全部 12 阶 FEM 模态，频率范围约 529–8935 Hz；BEM 边界从 448 加密至 1792 个面片，以七点五次精度 Dunavant 积分替换三点积分。对两个未用于拟合的半径上的 480 个点验证。

## 实测

- 12 个模态独立点复声压相对 BEM 误差：0.292%、0.316%、0.135%、0.356%、0.391%、0.275%、0.371%、0.537%、0.621%、0.891%、0.555%、0.941%。
- 三听者音频相对 BEM 的合计 L2 误差：0.282%。新增六段 48 kHz、3 秒 WAV，保留统一播放增益和原始声压。
- 模态 1、6、12 的单层/多层实际拟合时间比约 4.78、3.04、3.45。两种算法均使用相同目标阈值和候选数量，但随机筛选路径与最终中心数可不同；这是本机单次观察，不是公平重复测速的统计结论，更不是论文 7000 倍运行时渲染加速的复现。
- 同三模态的 448/1792 面片 BEM 结果差异分别为 2.20%、1.95%、4.12%。BEM 离散误差仍明显大于 PAT 的逼近误差。
- 解析球校验新增 1800 Hz 的 l=1、m=0 非均匀边界条件；80/320/1280 面片误差依次 4.73%、3.67%、2.25%。400 Hz 的 l=0 校验仍非全程单调，1280 面片误差 1.65%，没有隐去粗网格的误差抵消现象。

结果图：[validation.png](../outputs/pat_extended/validation.png)。详细数字：[extended-metrics.json](extended-metrics.json)。全部传递系数、密度、偏移面、边界网格、独立查询结果和原始音频位于 `../outputs/pat_extended/`。

音频：[PAT x](../outputs/pat_extended/pat_x.wav)、[PAT y](../outputs/pat_extended/pat_y.wav)、[PAT z](../outputs/pat_extended/pat_z.wav)；[BEM x](../outputs/pat_extended/bem_x.wav)、[BEM y](../outputs/pat_extended/bem_y.wav)、[BEM z](../outputs/pat_extended/bem_z.wav)。

## 仍有的界限

此实验覆盖了原论文的核心单层与多层传递近似流程，但输入仍为自建粗 FEM 小梁。未取得原论文商用 Neo Acoustics 和原始铃、龙、薄壳兔/椅场景完整数据，没有复现原论文表格。当前间接单层 BEM 未加入 CHIEF 或 Burton–Miller 内共振处理；五次积分也不等于近奇异积分已完全解决。音频按论文忽略传递相位，不能代替完整瞬态空气传播。

偏移面网格小于本例最短波长的约 1/7，源处于实体内且听者在偏移面外；不将该设置泛化为任意几何或高频可用。额外依赖 PyMCubes 0.1.4 已安装在 `.conda/acoustics`，对应安装日志保留。

若从前轮 Conda 显式清单恢复环境，另执行 `.\.conda\acoustics\python.exe -m pip install -r .\02_PAT\docs\requirements-extended.txt`，再运行扩展入口。
