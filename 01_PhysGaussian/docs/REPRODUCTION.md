# PhysGaussian 当前复现记录

完整原始透视 SH CUDA 渲染与 MPM 已实际运行；本地 Linux Conda 环境位于 WSL Ubuntu1 `/opt/3dgs-runtime/envs/physgaussian`。Python 3.9、PyTorch 2.0+cu118、CUDA Toolkit 11.8、Warp 0.10.1、Taichi 1.5.0，原始 rasterizer 与 simple-knn 均编译成功。

- [官方完整场景及视频](OFFICIAL_SCENES.md)：原模型、相机、配置；逐帧状态与最终全粒子状态保存。
- [原始图像到 3DGS 的重建训练](RECONSTRUCTION.md)：30,000 步，独立 200 测试视图指标。
- [材料核独立审计](MATERIAL_AUDIT.md)：弹性、塑性核检查及 snow 缺失分支。
- [基础梁验证](RESULTS.md) 和 [短时 Ficus 诊断](FICUS_RESULTS.md)：保留早期数值对照，不与最终 SH 渲染混淆。
- [所有模型与检查点](model-resources.json)、[公开模型下载记录](official-model-downloads.json)。

上游提交 PhysGaussian `8339ed6aa2cd5d50e1001a254a3d95aea678a956`；3DGS `d9fad7b3450bf4bd29316315032d57157e23a515`；rasterizer `59f5f77e3ddbac3ed9db93ec2cfe99ed6c5d121d`；simple-knn `44f764299fa305faf6ec5ebd99939e0508331503`。跟踪源码未修改，适配在仓库外。

必要适配：Taichi 硬编码 8 GiB 申请限至 0.5 GiB；关闭仿真时梯度；旧 Warp CUDA 注释使用 ASCII 源码软链接；增加 WSL libcuda 搜索路径。没有用正交诊断渲染替代最终 SH 结果，没有为成功而缩短完整场景。原 Windows 失败和 Linux 安装失败保留在 logs 中。

当前命令见 [统一环境说明](../../复跑与环境说明.md)。Linux 包清单为 `environment-linux.yml`、`conda-explicit-linux64.txt`、`requirements-linux-lock.txt`；旧 Windows 基线环境也保留。详细早期实验参数和失败诊断见 [归档记录](BASELINE_REPRODUCTION.md)，其中“未编译/未运行原渲染”的描述只适用于当时，现已解决。

有限值、质量守恒和视频可读是基础审计，不证明论文全部材料的实验准确性或性能。F_trial 在塑性材料中不是最终弹性 F；未把三篇论文连接成同物体的声画物理系统。许可保留于各原代码目录，不以本次运行扩大上游再分发许可。

## 完成性复核

- [高斯协方差、旋转和增量输运](GAUSSIAN_TRANSPORT.md)
- [各向异性正则完整实验](ANISOTROPY_RESULTS.md)
- [SH 坐标系独立审计](SH_FRAME_AUDIT.md)
- [SH 修复三场景同状态对照](SH_CORRECTED_SCENES.md)
