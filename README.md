# 3DGS 物理与声音复现实验

PhysGaussian / Precomputed Acoustic Transfer (PAT) / NeuralSound，按三篇论文分目录。

**最新：2026-11-02 补做了上一轮的 5 项失败 + 6 项未验证。该 11 项现在为 6 通过、1 失败、4 未验证，仍不能称为三篇论文完整复现成功。** 通过只限报告注明的本地修复或执行范围；不能将新增原型当作照片 3DGS—MPM 接触—神经声音完整系统。

## 队友先看这里

1. 下载 [本轮轻量效果包](https://github.com/xch1234/3dgs-physics-acoustics-reproduction/releases/download/remediated-2026-11-02/remediation-viewing-demo.zip)，完整解压后用 Edge / Chrome 双击 `本轮查看效果.html`。无需 Conda/CUDA，可看 19 段视频和 24 个 WAV。
2. 阅读[补做验收报告](remediation_20261101/补做验收报告.md)、[结果查看指南](remediation_20261101/本轮结果查看指南.md)和[视觉核查](remediation_20261101/可视化人工核查.md)。
3. 查[全部命令与输出](remediation_20261101/命令与输出索引.md)；初次失败和后续恢复记录均保留。

GitHub 文件页不执行 HTML；请下载效果包或整个仓库 ZIP 后本地打开。新 [Release](https://github.com/xch1234/3dgs-physics-acoustics-reproduction/releases/tag/remediated-2026-11-02) 提供完整模型、数组、逐帧图与恢复清单，轻量效果包只用于观看。

## 实际结果和限制

- 修复环境导出、本地相位不变性、SH 坐标计算和 snow 本构；完整重跑训练、渲染、200 图评估与扩展场景。新环境优先使用 Conda。
- 神经声辐射仍未达高精度：400 epoch 模型平均原始相对 L2 为 88.96%，最坏 967.70%。能训练、能发声不等于精度通过。
- 完整 PAT 基准、三论文原始数据/架构/性能与听感、另一台机器恢复、完整统一系统仍未验证。
- 新各向异性模型 200 图 PSNR 34.2856 / SSIM 0.985903 / LPIPS 0.0128053，静态图片指标未优于基线；约束轴长比属于另一目标。

## 获取代码和完整结果

```bash
git clone https://github.com/xch1234/3dgs-physics-acoustics-reproduction.git
cd 3dgs-physics-acoustics-reproduction
python tools/fetch_upstream.py --list
python tools/fetch_upstream.py
# 先列出本轮产物
python tools/restore_artifacts.py --manifest sharing/remediation-artifacts.json --list
# 按需恢复某一训练结果（含 SHA-256 检查，不覆盖不同内容）
python tools/restore_artifacts.py --manifest sharing/remediation-artifacts.json --prefix remediation_20261101/physics/outputs/ficus_anisotropy/
# 全部本轮大文件：添加 --all；先留足磁盘空间
```

恢复工具需要 Python 3.11+，只用标准库；不会自动安装环境或启动训练。原 Windows/WSL 绝对路径是执行证据，换电脑时需按实际路径调整。见[本轮发布范围与恢复说明](sharing/本轮补做发布说明.md)。

## 目录与历史

- [01_PhysGaussian](01_PhysGaussian/README.md)、[02_PAT](02_PAT/README.md)、[03_NeuralSound](03_NeuralSound/README.md)：论文各自的代码与历史资料；本轮修改后的本地包装器和 YAML 已同步。
- [remediation_20261101](remediation_20261101/README.md)：本轮修复、训练、检查、失败及恢复证据。
- [2026-11-01 独立验证](verification_20261101/独立验证报告.md)：历史 32 项结论保留，不以新文档改写旧实验。
- [旧 Release](https://github.com/xch1234/3dgs-physics-acoustics-reproduction/releases/tag/verified-2026-11-01)、[旧效果页](查看效果.html)、[旧查看与复跑指南](查看与复跑指南.md)：明确作为历史快照。

作者源码按固定提交下载，新增修复位于本地包装器/适配器。Conda 安装目录、缓存、可重新下载的作者数据和模型不上传。来源与许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
