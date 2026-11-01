# 官方完整场景运行结果

来源：未修改的 `gs_simulation.py`、官方模型与场景配置。以下只列出保存了最终指标且通过产物检查的运行。

通用适配：Taichi 申请从 8 GiB 限为 0.5 GiB；关闭梯度；ASCII 源码软链接绕过 Warp 0.10 的路径编码限制；补充 WSL libcuda 搜索路径。逐帧检查粒子位置、变形梯度有限及总质量保持。

六个 official_full 场景使用作者发布的最高迭代 PLY。若列出 ficus_reconstructed_full，则使用本项目重新训练 30,000 步且独立评估的 Ficus，详见 RECONSTRUCTION.md。这里仅汇总动态模拟；外观 PSNR/SSIM/LPIPS 另行计算。显存指标仅统计 PyTorch，不含 Warp/Taichi；计时包含审计，部分场景与 CPU 参考计算并行，Wolf 期间还在确认显存余量后执行过短时网络推理，不能当论文性能。

## bread_official_full

- 182,959 粒子，30,000 子步，3 秒；300 帧，1000×1000。
- 最大位移 0.6088159（MPM 坐标单位），全程最小 det(F_trial)=0.1210127；总用时 344.3 秒。
- 检查点：`iteration_30000`，SHA256 `07e019407e920932094af67acb90b9fe8b37d1206a0724926dc117cb4d12b1bf`。
- [视频](../outputs/bread_official_full/output.mp4) · [四帧预览](../outputs/bread_official_full/contact_sheet.jpg) · [状态曲线](../outputs/bread_official_full/state_audit.pdf) · [完整指标](../outputs/bread_official_full/metrics.json)

## bread_sh_corrected

- 182,959 粒子，30,000 子步，3 秒；300 帧，1000×1000。
- 最大位移 0.6088783（MPM 坐标单位），全程最小 det(F_trial)=0.1216518；总用时 343.5 秒。
- 检查点：`iteration_30000`，SHA256 `07e019407e920932094af67acb90b9fe8b37d1206a0724926dc117cb4d12b1bf`。
- [视频](../outputs/bread_sh_corrected/output.mp4) · [四帧预览](../outputs/bread_sh_corrected/contact_sheet.jpg) · [状态曲线](../outputs/bread_sh_corrected/state_audit.pdf) · [完整指标](../outputs/bread_sh_corrected/metrics.json)

## ficus_anisotropy_full

- 251,596 粒子，50,000 子步，5 秒；125 帧，800×800。
- 最大位移 0.2940186（MPM 坐标单位），全程最小 det(F_trial)=0.9700018；总用时 428.6 秒。
- 检查点：`iteration_30000`，SHA256 `7d02a670a912af097b60abf7856f2c081f7205eb11ddd4a63c147f939c0e87ef`。
- [视频](../outputs/ficus_anisotropy_full/output.mp4) · [四帧预览](../outputs/ficus_anisotropy_full/contact_sheet.jpg) · [状态曲线](../outputs/ficus_anisotropy_full/state_audit.pdf) · [完整指标](../outputs/ficus_anisotropy_full/metrics.json)

## ficus_official_full

- 171,553 粒子，50,000 子步，5 秒；125 帧，800×800。
- 最大位移 0.1819591（MPM 坐标单位），全程最小 det(F_trial)=0.9811099；总用时 352.2 秒。
- 检查点：`iteration_60000`，SHA256 `20fe2cb4709936029b32daaee3c28f2eb0e3d6962da06793e919049fb9595a8e`。
- [视频](../outputs/ficus_official_full/output.mp4) · [四帧预览](../outputs/ficus_official_full/contact_sheet.jpg) · [状态曲线](../outputs/ficus_official_full/state_audit.pdf) · [完整指标](../outputs/ficus_official_full/metrics.json)

## ficus_reconstructed_full

- 215,654 粒子，50,000 子步，5 秒；125 帧，800×800。
- 最大位移 0.2355251（MPM 坐标单位），全程最小 det(F_trial)=0.9748012；总用时 363.1 秒。
- 检查点：`iteration_30000`，SHA256 `2d885267faa054bb842c8a86c5d27c6dba1fd485a6fee6afa9b4e525b0066697`。
- [视频](../outputs/ficus_reconstructed_full/output.mp4) · [四帧预览](../outputs/ficus_reconstructed_full/contact_sheet.jpg) · [状态曲线](../outputs/ficus_reconstructed_full/state_audit.pdf) · [完整指标](../outputs/ficus_reconstructed_full/metrics.json)

## pillow2sofa_official_full

- 695,984 粒子，60,000 子步，6 秒；300 帧，1000×1000。
- 最大位移 0.7282355（MPM 坐标单位），全程最小 det(F_trial)=0.08881886；总用时 1298.6 秒。
- 检查点：`iteration_60000`，SHA256 `7ac0be91d634d6a0b53fb5dde23fb2c2aca7f30ba357173fb0951b66b2b3162a`。
- [视频](../outputs/pillow2sofa_official_full/output.mp4) · [四帧预览](../outputs/pillow2sofa_official_full/contact_sheet.jpg) · [状态曲线](../outputs/pillow2sofa_official_full/state_audit.pdf) · [完整指标](../outputs/pillow2sofa_official_full/metrics.json)

## plane_official_full

- 67,260 粒子，40,000 子步，4 秒；400 帧，1060×1895。
- 最大位移 0.6227539（MPM 坐标单位），全程最小 det(F_trial)=0.9444005；总用时 682.2 秒。
- 检查点：`iteration_30000`，SHA256 `1ff04607704ec94ba082efa20a803aac29cbe481884fefb5db9fa460e97e0f03`。
- [视频](../outputs/plane_official_full/output.mp4) · [四帧预览](../outputs/plane_official_full/contact_sheet.jpg) · [状态曲线](../outputs/plane_official_full/state_audit.pdf) · [完整指标](../outputs/plane_official_full/metrics.json)

## plane_sh_corrected

- 67,260 粒子，40,000 子步，4 秒；400 帧，1060×1895。
- 最大位移 0.6227539（MPM 坐标单位），全程最小 det(F_trial)=0.9444248；总用时 879.2 秒。
- 检查点：`iteration_30000`，SHA256 `1ff04607704ec94ba082efa20a803aac29cbe481884fefb5db9fa460e97e0f03`。
- [视频](../outputs/plane_sh_corrected/output.mp4) · [四帧预览](../outputs/plane_sh_corrected/contact_sheet.jpg) · [状态曲线](../outputs/plane_sh_corrected/state_audit.pdf) · [完整指标](../outputs/plane_sh_corrected/metrics.json)

## vasedeck_official_full

- 55,364 粒子，30,000 子步，3 秒；75 帧，3994×2995。
- 最大位移 0.9558322（MPM 坐标单位），全程最小 det(F_trial)=0.862554；总用时 412.6 秒。
- 检查点：`iteration_30000`，SHA256 `ebaab02f06e21197a5af5bc0870b6f6b1f9c044a8817e272ae76394eba633142`。
- [视频](../outputs/vasedeck_official_full/output.mp4) · [四帧预览](../outputs/vasedeck_official_full/contact_sheet.jpg) · [状态曲线](../outputs/vasedeck_official_full/state_audit.pdf) · [完整指标](../outputs/vasedeck_official_full/metrics.json)

## vasedeck_sh_corrected

- 55,364 粒子，30,000 子步，3 秒；75 帧，3994×2995。
- 最大位移 0.9558312（MPM 坐标单位），全程最小 det(F_trial)=0.8625628；总用时 642.4 秒。
- 检查点：`iteration_30000`，SHA256 `ebaab02f06e21197a5af5bc0870b6f6b1f9c044a8817e272ae76394eba633142`。
- [视频](../outputs/vasedeck_sh_corrected/output.mp4) · [四帧预览](../outputs/vasedeck_sh_corrected/contact_sheet.jpg) · [状态曲线](../outputs/vasedeck_sh_corrected/state_audit.pdf) · [完整指标](../outputs/vasedeck_sh_corrected/metrics.json)

## wolf_official_full

- 188,201 粒子，99,950 子步，1.999 秒；50 帧，800×800。
- 最大位移 1.051405（MPM 坐标单位），全程最小 det(F_trial)=0.9935697；总用时 3016.1 秒。
- 检查点：`iteration_30000`，SHA256 `c23a8f36662ac47445bd4a4e3d6faea6b97bdbc8d6f7934921eccce459651f8b`。
- [视频](../outputs/wolf_official_full/output.mp4) · [四帧预览](../outputs/wolf_official_full/contact_sheet.jpg) · [状态曲线](../outputs/wolf_official_full/state_audit.pdf) · [完整指标](../outputs/wolf_official_full/metrics.json)

## 判读边界

三个 *_sh_corrected 场景另加了 SH 旋转坐标基转换。每帧保存同一物理状态的原版/修复版图像差异；不是未修改渲染行为，详见 SH_CORRECTED_SCENES.md。

ficus_anisotropy_full 若出现，使用单独训练的式(12)正则化模型，阈值5、权重0.01为本地预定值。它不是作者发布模型或原图8场景；见 ANISOTROPY_RESULTS.md。

Wolf 保留上游 `step_per_frame = int(frame_dt / substep_dt)`：Python 浮点下 0.04 / 2e-5 略小于 2000，截断为每帧 1999 步。因此原 50 帧实际为 99,950 子步、1.999 秒，视频仍为 25 fps / 2 秒。这是原代码行为，不是本次人为减少步数；未修改上游计算以凑名义数值。

有限值和质量守恒是基础数值检查，不等于物理模型已由实验测量验证。塑性或颗粒场景中的 F_trial 也不能直接当作最终弹性变形梯度。原始配置失败及适配运行应分别查阅日志与继续执行记录。
