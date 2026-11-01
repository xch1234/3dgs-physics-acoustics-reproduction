# 3DGS 物理与声音复现实验

最快查看：下载 [viewing-demo.zip](https://github.com/xch1234/3dgs-physics-acoustics-reproduction/releases/download/verified-2026-11-01/viewing-demo.zip)，解压后双击 `查看效果.html`。该轻量包包含全部页面媒体；完整代码请下载仓库。

PhysGaussian / Precomputed Acoustic Transfer (PAT) / NeuralSound 的本地实验、运行记录与独立验证。面向队友分享，按三篇论文分目录。

**当前结论：局部模块和本地流程可复现；不能称为三篇论文完整复现成功。** 2026-11-01 独立验证共 32 项：21 通过、5 失败、6 未验证。历史报告中的“完成”不替代独立验收。

## 先看效果（不用安装训练环境）

1. 点击 GitHub 的 **Code → Download ZIP**，解压。
2. 用 Edge / Chrome 双击打开根目录 **[查看效果.html](查看效果.html)**。页面包含 12 段模拟视频、声学音频、重建对照和神经预测图，无需运行服务器。
3. 想自由旋转 3DGS：从 [Releases](https://github.com/xch1234/3dgs-physics-acoustics-reproduction/releases/tag/verified-2026-11-01) 下载 `ficus-30000.ply`，在支持 Gaussian Splat PLY 的查看器中打开；详见 [查看与复跑指南](查看与复跑指南.md)。

GitHub 文件页不会执行 HTML；请下载后打开。下载仓库 ZIP 不包含 Releases 的大文件，但已包含直接观看所需的视频、音频和摘要图。

## 验证结果与证据

- [独立验证报告：原始目标、逐项通过/失败/未验证](verification_20261101/独立验证报告.md)
- [83 条命令与日志索引](verification_20261101/命令与日志索引.md)
- [可视化核查](verification_20261101/可视化核查记录.md)
- [验收标准](verification_20261101/验收标准.md)

实际新跑 Ficus：30,000 次训练、200 张测试渲染，PSNR 34.8506 / SSIM 0.98719 / LPIPS 0.01172；物理模拟 50,000 子步、125 帧。这些是本地 Ficus 指标，不是论文完整场景基准。

仍存在环境导出路径损坏、声学等价模态基不变性失败、原 SH 坐标变换失败、snow 应力分支缺失和本地辐射预测精度不足。完整论文数据、全训练重复、速度与听感基准等仍未验证。

## 目录

- [01_PhysGaussian](01_PhysGaussian/README.md)：本地包装代码、MPM/3DGS 结果、视频、重建与材料检查。
- [02_PAT](02_PAT/README.md)：FEM/BEM/PAT 本地链路、音频、数值与 C++ 核检查。
- [03_NeuralSound](03_NeuralSound/README.md)：训练包装、预测、音频、误差与检查点记录。
- `verification_20261101/`：独立验证代码、原始命令、日志、报告和摘要图。
- `reproduction/`：基础模态实验和历史执行/审计工具。
- `tools/`、`sharing/`：固定版本上游获取、大文件恢复、发布清单。

## 获取代码与完整产物

```bash
git clone https://github.com/xch1234/3dgs-physics-acoustics-reproduction.git
cd 3dgs-physics-acoustics-reproduction
python tools/fetch_upstream.py --list
python tools/fetch_upstream.py
python tools/restore_artifacts.py --list --prefix verification_20261101/outputs/ficus_fresh_30000/
# 按需下载；恢复路径与原工作目录一致，SHA-256 校验，不覆盖不同内容
python tools/restore_artifacts.py --prefix verification_20261101/outputs/ficus_fresh_30000/
```

辅助脚本需要 Python 3.11+，仅使用标准库。它们不安装 CUDA/Conda，也不启动训练。完整恢复用 `--all`，先阅读 [发布范围](sharing/发布范围.md)，留足磁盘空间。上游数据与作者预训练模型按原始下载脚本获取。新机器完整环境重建尚未验收，不能保证克隆后一键重训。

## 来源与许可

上游源码使用固定提交获取，不将作者仓库冒充本项目原创。论文 PDF、Conda 安装目录、运行缓存和可重新下载的作者数据/预训练模型不重复上传。各来源、版本和权利说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。公开仓库不代表所有第三方内容可商用。
