> 发布说明：下文为历史实验记录。当前验收结论以 [独立验证报告](../verification_20261101/独立验证报告.md) 为准；不能据此认定三篇论文完整复现成功。大文件由 Releases 按原路径恢复。

# PhysGaussian

已完成官方完整场景模拟与透视 SH CUDA 渲染、Ficus 30,000 步外观训练和独立视图指标，并保留基础 MPM 数值与材料核验证。

- [复现记录](docs/REPRODUCTION.md)
- [官方场景视频与状态审计](docs/OFFICIAL_SCENES.md)
- [原始图像重建与测试](docs/RECONSTRUCTION.md)
- [材料检查](docs/MATERIAL_AUDIT.md)

入口 `run_scenes.ps1`、`run_reconstruction.ps1`；基线入口 `run.ps1`、`run_ficus.ps1`。完整环境与命令见根目录 [说明](../复跑与环境说明.md)。

## 完成性复核

- [高斯协方差、旋转和增量输运](docs/GAUSSIAN_TRANSPORT.md)
- [各向异性正则完整实验](docs/ANISOTROPY_RESULTS.md)
- [SH 坐标系独立审计](docs/SH_FRAME_AUDIT.md)
- [SH 修复三场景同状态对照](docs/SH_CORRECTED_SCENES.md)
