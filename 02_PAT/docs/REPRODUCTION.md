# PAT 复现记录

日期：2026-11-01（Asia/Shanghai）。已完成自建小场景核心流程及 §4.3.2 多层算法扩展，尚未完成原论文全场景和性能指标复现。下面保留首轮配置说明；扩展结果见 [EXTENDED_RESULTS.md](EXTENDED_RESULTS.md)。

后续还完成 [移动听者](MOVING_LISTENER.md)、[ModalSound C++ 基函数](MODALSOUND_BASIS.md) 和 [ModalSound C++ 四面体 FEM](MODALSOUND_FEM.md)。两项 C++ 验证实际编译调用上游代码，不是仅阅读仓库；完整 Qt/FastBEM 工具链仍未构建。声学离散误差与作者 Bempp 差异见 [跨实现核查](../../03_NeuralSound/docs/BEM_CROSSCHECK.md)，不能把低 PAT 拟合误差当作真实声场的同等精度。

## 方法来源

论文在 `../paper/PAT_2006.pdf`。论文 §3 明确可以用任何标准声学求解器预计算声场，原实验使用 Neo Acoustics 商用 BEM。这里自建常面元间接 BEM；不是取得了原商用求解器或作者完整代码。

`../code/ModalSound` 是 SIGGRAPH 2016 教学仓库，提交 `1af5e40893d0ad1b73b594a0cba7a5466b4fc56d`，保持未修改。它包含从 FastBEM 结果生成多极子矩的工具，但不提供完整可运行的 FastBEM 数据链。后续已经实际编译并用解析边界迹运行其积分、矩生成、二进制保存和求值，见 [原后处理验证](MODALSOUND_TRANSFER.md)；未取得 FastBEM 求解器，也未安装旧 C++ 图形工具链。

## 核心链路及对应论文

1. 使用 NeuralSound 官方传统 FEM 算出的六阶塑料梁模态，见 `../inputs/official_fem_result.npz`。输入来源为本项目 `03_NeuralSound/code/run_official_fem.py`，不是论文原模型。
2. 按 §3 的 Helmholtz / Neumann 声辐射方程计算边界密度，采用 e^(+iωt) 和 outgoing e^(-ikr) 约定。正常位移导出压力导数 ρω²(n·φ)。
3. 在包围物体的半径 0.11 m 球面采样 BEM 复声压，作为 §4.2 的偏移面 Dirichlet 拟合目标。
4. 按 §4.1 用每中心四项 l=0,1 的球 Hankel 第二类函数 × 球谐基表示声场。
5. 按 §4.3.1 以候选子空间对残差的投影评分选择中心，按 §4.2 面积加权，采用相对阈值 1e-6 的截断 SVD 重拟合。
6. 在未用于拟合的 360 个外部点比较复声压；在三个听者位置用 §3 的 |p(x)|q(t) 近似合成声压音频，忽略传递相位。

所有实现位于 `../code/run_pat.py`，为本地重写；不是运行 ModalSound 的系数读取器。旧质量弹簧可听化保存在 `../code/modal_baseline`，它不是本轮 PAT 声辐射结果。

## 验证与首轮失败记录

- BEM 在 400 Hz、半径 0.05 m 脉动球上与独立解析球 Hankel 解比较。
- 首轮对误差“从最粗到最细严格降低”的断言失败：80 面片误差偶然很小，320 面片上升，1280 面片下降。原始日志保留为 `../logs/pat-first-validation-failure.log`。
- 未隐去这组数据，也未声称已证明网格单调收敛。最终检查要求 1280 面片解析误差小于 3%，并低于 320 面片；另保留梁第一模态粗细网格差异。
- 固定随机种子 20261101、80 个内部候选中心，每模态最多 24 个中心，偏移面拟合目标 2%；独立点误差与拟合误差分别报告。
- 平面单层法自项为 -1/2，法向核 K' 的共面自项为零，其余三点积分；未实现高频 / 内共振稳健处理，因此必须保留适用范围。

最终实测数字、图和音频说明见 `RESULTS.md`；完整参数与检查数字见 `metrics.json`。

## 运行与环境

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\02_PAT\run.ps1
```

环境为项目根 `.conda/acoustics`，CPU 单线程。精确恢复文件见本目录 `conda-explicit-win64.txt` / `environment.yml`。
输入已单独保存，PAT 入口不必再次运行另一个文件夹；需要更新梁输入时，重新运行 `03_NeuralSound/run.ps1` 后复制新 FEM 文件并记录版本。
固定输入的 SHA256 与来源保存在 `input-provenance.json`。该记录不会随 NeuralSound 重跑自动更新；有意修改场景时需同步此记录及 PAT 的几何假设。归档时已核对两份 NPZ 完全相同；后续审计检查归档哈希，不要求新运行的压缩文件字节相同（ZIP 时间戳及重根模态基可能变化）。

## 未完成部分

继续执行后，已完成距离场 / marching cubes 偏移面、三层随机 source placement、九项多极子、12 阶模态及单层/多层比较，详见扩展报告。尚未复现复杂薄壳或龙模型、全模态音色和原论文 7000 倍加速结果。当前误差是相对本地 BEM 离散参考的逼近误差，不是真实声压精度；BEM 自身存在离散误差。
当前音频有声辐射求解，区别于上轮“振动可听化”；但使用有限模态、局部线性材料和忽略相位的论文近似，不是完整时域空气传播。
