> 2026-11-02 更新：本轮 11 项补做结果为 6 通过 / 1 失败 / 4 未验证，详见[最新报告](../remediation_20261101/补做验收报告.md)与[本轮查看指南](../remediation_20261101/本轮结果查看指南.md)。下文历史结果按原日期保留。

> 发布说明：下文为历史实验记录。当前验收结论以 [独立验证报告](../verification_20261101/独立验证报告.md) 为准；不能据此认定三篇论文完整复现成功。大文件由 Releases 按原路径恢复。

# Precomputed Acoustic Transfer 复现

2026-11-01。已完成小梁的 FEM → BEM → 多极子拟合 → 音频链路、距离场偏移面、多层随机候选筛选、12 模态及移动听者实验，并实际验证 ModalSound C++ 声学基函数和四面体 FEM。未复现原论文复杂场景全集与速度数字。

- [12 模态与多层算法](docs/EXTENDED_RESULTS.md)：`run_extended.ps1`
- [移动听者与规模测试](docs/MOVING_LISTENER.md)：`run_additional.ps1 -Task moving`
- [真实 C++ 多极子基函数](docs/MODALSOUND_BASIS.md)：`run_additional.ps1 -Task basis`
- [真实 C++ 四面体 FEM](docs/MODALSOUND_FEM.md)：`run_fem.ps1`
- [真实 C++ 边界积分与多极子矩生成/二进制读回](docs/MODALSOUND_TRANSFER.md)：`code/run_modalsound_transfer.sh`；解析边界迹测试，不是 FastBEM 求解器输出。

以下保留六模态基础实验入口与音频。

- [完整复现记录](docs/REPRODUCTION.md) · [实测结果](docs/RESULTS.md)
- [验证图](outputs/pat_pipeline/validation.png) · [方向图](outputs/pat_pipeline/directivity.png)
- PAT 音频：[x 听者](outputs/pat_pipeline/pat_listener_x.wav)、[y 听者](outputs/pat_pipeline/pat_listener_y.wav)、[z 听者](outputs/pat_pipeline/pat_listener_z.wav)
- BEM 参考：[x 听者](outputs/pat_pipeline/bem_listener_x.wav)、[y 听者](outputs/pat_pipeline/bem_listener_y.wav)、[z 听者](outputs/pat_pipeline/bem_listener_z.wav)

在项目根目录执行，使用 `.conda/acoustics`，仅 CPU：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\02_PAT\run.ps1
```

`code/run_pat.py` 与扩展脚本是本地方法实现；`code/ModalSound/` 是实际调用部分数值核的 2016 教学仓库，不是 PAT 2006 官方完整代码。`code/modal_baseline/` 保留此前的质量弹簧可听化，不能替代这里的声辐射实验。FEM 输入已保存在本文件夹，可独立重跑。
