> 发布说明：下文为历史实验记录。当前验收结论以 [独立验证报告](verification_20261101/独立验证报告.md) 为准；不能据此认定三篇论文完整复现成功。大文件由 Releases 按原路径恢复。

# 当前复现状态

更新时间：2026-11-01T12:17+08:00。本文件只按实际产物记录；脚本已准备不算实验完成。

## PhysGaussian

- ficus_official_full：通过保存结果检查，[指标](01_PhysGaussian/outputs/ficus_official_full/metrics.json)。
- bread_official_full：通过保存结果检查，[指标](01_PhysGaussian/outputs/bread_official_full/metrics.json)。
- pillow2sofa_official_full：通过保存结果检查，[指标](01_PhysGaussian/outputs/pillow2sofa_official_full/metrics.json)。
- plane_official_full：通过保存结果检查，[指标](01_PhysGaussian/outputs/plane_official_full/metrics.json)。
- vasedeck_official_full：通过保存结果检查，[指标](01_PhysGaussian/outputs/vasedeck_official_full/metrics.json)。
- wolf_official_full：通过保存结果检查，[指标](01_PhysGaussian/outputs/wolf_official_full/metrics.json)。
- ficus_reconstruction：通过保存结果检查，[指标](01_PhysGaussian/outputs/ficus_reconstruction/metrics.json)。
- ficus_reconstructed_full：通过保存结果检查，[指标](01_PhysGaussian/outputs/ficus_reconstructed_full/metrics.json)。
- gaussian_transport：通过保存结果检查，[指标](01_PhysGaussian/outputs/gaussian_transport/metrics.json)。
- ficus_anisotropy：通过保存结果检查，[指标](01_PhysGaussian/outputs/ficus_anisotropy/metrics.json)。
- ficus_anisotropy_full：通过保存结果检查，[指标](01_PhysGaussian/outputs/ficus_anisotropy_full/metrics.json)。
- bread_sh_corrected：通过保存结果检查，[指标](01_PhysGaussian/outputs/bread_sh_corrected/metrics.json)。
- plane_sh_corrected：通过保存结果检查，[指标](01_PhysGaussian/outputs/plane_sh_corrected/metrics.json)。
- vasedeck_sh_corrected：通过保存结果检查，[指标](01_PhysGaussian/outputs/vasedeck_sh_corrected/metrics.json)。

## PAT

- pat_pipeline：已有实际结果。
- pat_extended：已有实际结果。
- moving_listener：已有实际结果。
- modalsound_basis：已有实际结果。
- modalsound_fem：已有实际结果。
- modalsound_transfer：已有实际结果。

## NeuralSound

- official_fem：已有实际最终结果，[指标](03_NeuralSound/outputs/official_fem/metrics.json)；精度须按其中数值判读。
- official_example：已有实际最终结果，[指标](03_NeuralSound/outputs/official_example/metrics.json)；精度须按其中数值判读。
- vibration_training：已有实际最终结果，[指标](03_NeuralSound/outputs/vibration_training/metrics.json)；精度须按其中数值判读。
- radiation_training：已有实际最终结果，[指标](03_NeuralSound/outputs/radiation_training/metrics.json)；精度须按其中数值判读。
- neural_audio：已有实际最终结果，[指标](03_NeuralSound/outputs/neural_audio/metrics.json)；精度须按其中数值判读。
- example_hybrid_ood：已有实际最终结果，[指标](03_NeuralSound/outputs/example_hybrid_ood/metrics.json)；精度须按其中数值判读。
- example_hybrid_ood_extended：已有实际最终结果，[指标](03_NeuralSound/outputs/example_hybrid_ood_extended/metrics.json)；精度须按其中数值判读。
- example_acoustic_ood：已有实际最终结果，[指标](03_NeuralSound/outputs/example_acoustic_ood/metrics.json)；精度须按其中数值判读。
- vibration_paper_schedule：已有实际最终结果，[指标](03_NeuralSound/outputs/vibration_paper_schedule/metrics.json)；精度须按其中数值判读。
- radiation_paper_schedule：已有实际最终结果，[指标](03_NeuralSound/outputs/radiation_paper_schedule/metrics.json)；精度须按其中数值判读。
- 包含网络开销的振动计时：已有最终结果。

## 记录与边界

- [继续执行记录](继续复现执行记录.md) 保存调度、适配和失败记录；早期暂停属于历史调度，最终运行状态见该文末尾。
- [已完成振动网络报告](03_NeuralSound/docs/VIBRATION_RESULTS.md)、[官方完整场景](01_PhysGaussian/docs/OFFICIAL_SCENES.md)、[PAT 扩展](02_PAT/docs/EXTENDED_RESULTS.md)。
- 既定扩展实验产物已通过独立验证；最终内容见 [复现总报告](复现总报告.md) 与 [验证记录](扩展产物验证记录.md)。
- 这些本地实验不自动等同于完整 ABC、原 PAT 复杂场景、论文全数据/速度复现。
