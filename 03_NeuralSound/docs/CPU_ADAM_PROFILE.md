# 完整 AcousticNet 的 CPU Adam 适配与实测

公开源码实际实例化 311,180,810 个参数，两个 Encoder 都使用 ResNet34。RTX 2050 4GB 不能同时保存全部权重、梯度和 Adam 两组状态，因此保留完整网络、将 Adam 状态与更新移至 CPU。

首次训练完成第 1 轮并保存 best.pt / last.pt，但速度较慢。py-spy 20 秒、20 Hz 采样记录：训练样本中约 38% 位于每步参数 `.cpu().clone()`，约 20% 位于 CPU 分母计算，约 18% 位于梯度拷贝；另一个恰好覆盖 checkpoint 的采样中多数时间位于 GPU storage 到 CPU 的复制。原文件、日志及两个 speedscope JSON 均保留，不能把这些采样当完整运行精确时间分解。

06:22 停止本任务的训练进程，保留完整第 1 轮断点，放弃第 2 轮未保存进度。没有修改用户其他进程。之后从第 1 轮的模型、优化器、调度器和随机状态恢复。

## 等价改动

- 额外保留与 GPU 权重相同的 float32 CPU master 参数；每步只从 GPU 读取梯度，CPU 按原 Adam 公式更新，再复制回 GPU。避免每步重复读取同一份权重。
- CPU master 与一次可复用梯度缓冲使用 pinned memory；显式同步保证 CPU 计算不会读取尚未复制完的梯度。
- checkpoint 使用现成 CPU master；模型与 optimizer state 共用 storage，torch.save 不重复保存同一份参数。不改变模型层、损失、学习率、batch 或浮点精度。
- 已有旧断点没有 master 字段时，从其 GPU 权重建立 master，保持后续状态一致。

## 实际验证

`code/validate_cpu_adam.py` 在 CPU 和 CUDA 两种参数设备上，与 PyTorch Adam 进行 18 次相同梯度更新，并在第 9 步保存/恢复全部状态。CPU 参数最大差 0；CUDA 最大差 1.49e-8，小于预设 1e-6。参见 [机器可读结果](cpu-adam-master-reference.json) 和 `logs/cpu-adam-master-validation.log`。原初版 12 步 CPU 对照也保留。

这是执行/存储适配，不是不同的网络或改用 SGD。代价是多保存约 1.24GB CPU 参数；实际内存仍需检查。用户可从同一 final checkpoint 继续训练，稀疏 GPU 运算不保证跨机器逐比特一致。

## 06:29 文件系统适配

第 2 轮计算完成后，对大 checkpoint 的采样多次停留在文件 writer 创建与写入，NTFS 挂载路径成为另一处瓶颈。在 history.json 确认第 2 轮完整断点已保存后，停止本任务进程，保留第二段日志为 `radiation-training-master-ntfs.log`，从第 2 轮继续。

活动权重改存 `/opt/3dgs-runtime/checkpoints/neuralsound-radiation`，同样位于 F 盘的 WSL 虚拟磁盘内。最佳权重按验证分数原规则选择；完整断点每 5 轮及最终轮保存，用临时文件加原子 rename 避免半写入。逐轮 history 仍写项目；训练/测试结束后把 best.pt 和 last.pt 复制回项目。此调整只改变保存位置和频率，不改变训练数据/目标/模型选择。最终 elapsed_s 只计最后一次调用，前两段时间要结合日志，不冒充总训练墙钟。

## CPU 线程测量

800 万 float32 元素的相同 Adam 算术，在训练进程仍运行时，2/4/8/12 线程的八次中位时间分别约 32.37/19.84/15.13/14.63 ms。8 与 12 接近，后续采用 8 线程，保留其他核供数据处理。该局部测量只帮助配置线程，不等于整个训练也获得同样倍速。[原始测量](cpu-adam-thread-benchmark.json)。计划在下一个完整 5 轮断点后切换，不从半写入权重恢复。

06:40 已确认第 5 轮完整断点与 history 保存完毕后执行切换。之后实际命令为 `run_neural_linux.sh radiation --epochs 100 --resume --cpu-threads 8`，日志 `radiation-training-native-8threads.log`。第 5 轮验证 loss 1.233975；只以验证 loss 选择最佳模型，没有按测试误差调参。

## 06:46 原 batch size 实测通过，启动正式训练

实际峰值显存表明主要开销为固定参数/梯度，小数据的激活较少。对作者原 batch 40 进行完整前向、反向、梯度裁剪和一次 Adam 更新，峰值分配 2,535,731,200 字节、保留 2,556,428,288 字节；检查通过，见 [实测记录](acoustic-batch40-probe.json)。

因此原 batch 2 改归档为资源与稳定性试跑：7 轮历史、5 轮完整断点，未执行测试集。正式训练从同一固定种子重新开始，原 batch 40、100 轮，未续接试跑权重。每轮 96 模态随机打乱后按 drop_last 使用 80 个样本，两个 batch；与 batch 2 的更新次数不同，不能拼接损失曲线。正式日志为 `radiation-training-formal-batch40.log`。既保持了公开 batch 设定，也减少了此小数据上反复更新 3.11 亿参数的开销。正式结果只来自新的 radiation_training 目录。
