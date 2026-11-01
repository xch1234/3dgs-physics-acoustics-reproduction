# 当前复现状态

更新时间：2026-11-01T09:54+08:00。本文件只按实际产物记录；脚本已准备不算实验完成。

## PhysGaussian

- ficus_official_full：通过保存结果检查，[指标](../../../01_PhysGaussian/outputs/ficus_official_full/metrics.json)。
- bread_official_full：通过保存结果检查，[指标](../../../01_PhysGaussian/outputs/bread_official_full/metrics.json)。
- pillow2sofa_official_full：通过保存结果检查，[指标](../../../01_PhysGaussian/outputs/pillow2sofa_official_full/metrics.json)。
- plane_official_full：通过保存结果检查，[指标](../../../01_PhysGaussian/outputs/plane_official_full/metrics.json)。
- vasedeck_official_full：通过保存结果检查，[指标](../../../01_PhysGaussian/outputs/vasedeck_official_full/metrics.json)。
- wolf_official_full：通过保存结果检查，[指标](../../../01_PhysGaussian/outputs/wolf_official_full/metrics.json)。
- ficus_reconstruction：通过保存结果检查，[指标](../../../01_PhysGaussian/outputs/ficus_reconstruction/metrics.json)。
- ficus_reconstructed_full：通过保存结果检查，[指标](../../../01_PhysGaussian/outputs/ficus_reconstructed_full/metrics.json)。
- gaussian_transport：通过保存结果检查，[指标](../../../01_PhysGaussian/outputs/gaussian_transport/metrics.json)。
- ficus_anisotropy：尚无最终指标。
- ficus_anisotropy_full：尚无最终指标。
- bread_sh_corrected：尚无最终指标。
- plane_sh_corrected：尚无最终指标。
- vasedeck_sh_corrected：尚无最终指标。

## PAT

- pat_pipeline：已有实际结果。
- pat_extended：已有实际结果。
- moving_listener：已有实际结果。
- modalsound_basis：已有实际结果。
- modalsound_fem：已有实际结果。
- modalsound_transfer：已有实际结果。

## NeuralSound

- official_fem：已有实际最终结果，[指标](../../../03_NeuralSound/outputs/official_fem/metrics.json)；精度须按其中数值判读。
- official_example：已有实际最终结果，[指标](../../../03_NeuralSound/outputs/official_example/metrics.json)；精度须按其中数值判读。
- vibration_training：已有实际最终结果，[指标](../../../03_NeuralSound/outputs/vibration_training/metrics.json)；精度须按其中数值判读。
- radiation_training：已有实际最终结果，[指标](../../../03_NeuralSound/outputs/radiation_training/metrics.json)；精度须按其中数值判读。
- neural_audio：已有实际最终结果，[指标](../../../03_NeuralSound/outputs/neural_audio/metrics.json)；精度须按其中数值判读。
- example_hybrid_ood：已有实际最终结果，[指标](../../../03_NeuralSound/outputs/example_hybrid_ood/metrics.json)；精度须按其中数值判读。
- example_hybrid_ood_extended：已有实际最终结果，[指标](../../../03_NeuralSound/outputs/example_hybrid_ood_extended/metrics.json)；精度须按其中数值判读。
- example_acoustic_ood：已有实际最终结果，[指标](../../../03_NeuralSound/outputs/example_acoustic_ood/metrics.json)；精度须按其中数值判读。
- vibration_paper_schedule：已有实际最终结果，[指标](../../../03_NeuralSound/outputs/vibration_paper_schedule/metrics.json)；精度须按其中数值判读。
- radiation_paper_schedule：尚无最终指标；逐轮记录已到 34 轮。
- 包含网络开销的振动计时：已有最终结果。

## 记录与边界

- [继续执行记录](../../../继续复现执行记录.md) 保存调度、适配和失败记录；其中标明的暂停进程需要按最新记录恢复。
- [已完成振动网络报告](../../../03_NeuralSound/docs/VIBRATION_RESULTS.md)、[官方完整场景](../../../01_PhysGaussian/docs/OFFICIAL_SCENES.md)、[PAT 扩展](../../../02_PAT/docs/EXTENDED_RESULTS.md)。
- 最终报告在全部既定实验后由实际指标生成；当前总报告可能仍为归档前的基础阶段，不据此忽略新增产物。
- 这些本地实验不自动等同于完整 ABC、原 PAT 复杂场景、论文全数据/速度复现。
