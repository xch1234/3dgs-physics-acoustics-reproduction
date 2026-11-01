"""Generate current Chinese reports from completed experiment metrics only."""
import json
import runpy
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8-sig'))


def write(rel, text):
    (ROOT / rel).write_text(text.strip()+'\n', encoding='utf-8')


def main():
    runpy.run_path(str(ROOT/'03_NeuralSound/code/summarize_radiation.py'), run_name='__main__')
    stamp = datetime.now().astimezone().isoformat(timespec='minutes')
    scenes = read('01_PhysGaussian/docs/official-scenes-verified.json')
    rec = read('01_PhysGaussian/docs/reconstruction-metrics.json')
    vib = read('03_NeuralSound/docs/vibration-training-metrics.json')
    rad = read('03_NeuralSound/docs/radiation-training-metrics.json')
    aud = read('03_NeuralSound/docs/neural-audio-metrics.json')
    pat = read('02_PAT/docs/extended-metrics.json')
    mov = read('02_PAT/docs/moving-listener-metrics.json')
    expected_scenes = {f'{name}_official_full' for name in ('ficus', 'bread', 'pillow2sofa', 'plane', 'vasedeck', 'wolf')}
    expected_scenes.add('ficus_reconstructed_full')
    expected_scenes.add('ficus_anisotropy_full')
    expected_scenes.update(f'{name}_sh_corrected' for name in ('bread','plane','vasedeck'))
    assert {row['scene'] for row in scenes} == expected_scenes, 'Refresh the completed eleven-scene summary first.'
    assert rec['all_checks_passed'] and rec['iterations'] == 30000
    means = rec['evaluation']['mean']
    scene_lines = '\n'.join(f'- {s["scene"]}：{s["particles"]:,} 粒子，{s["frames"]} 帧，{s["simulation_seconds"]:g} 秒；[视频](01_PhysGaussian/outputs/{s["scene"]}/output.mp4)。' for s in scenes)
    write('复现总报告.md', f'''
# 三篇论文复现总报告

更新时间：{stamp}。代码、环境记录、实验输出分别保存在 `01_PhysGaussian`、`02_PAT`、`03_NeuralSound`。本报告以实际保存的结果为依据，早期仅跑基础模块的报告已归档。

## 可以验收的内容

PhysGaussian 已运行官方 `gs_simulation.py`、原始透视 SH CUDA 光栅器、MPM 和公开场景。最高迭代检查点用于完整模拟，逐帧保存粒子审计并复核视频帧数。

{scene_lines}

另外使用 Ficus 原始 800×800 图像重新训练上游 3DGS **30,000 步**，100 个训练视图、200 个独立测试视图：PSNR **{means['PSNR']:.4f} dB**、SSIM **{means['SSIM']:.6f}**、LPIPS-VGG **{means['LPIPS']:.6f}**。保留模型、checkpoint、全部测试渲染及逐图指标。[重建报告](01_PhysGaussian/docs/RECONSTRUCTION.md)。发布的旧 Ficus 模型 `eval=False`，不能把其图像当独立测试；这里指标只针对新训练模型。

PAT 已完成模态输入、Helmholtz BEM、距离场偏移面、九项多极子、三层随机候选筛选、独立空间点测试及冲量音频。12 阶、1,792 面片、4,568 个偏移采样点；PAT 与同一 BEM 的音频相对 L2 误差 **{pat['audio_relative_L2']*100:.4f}%**。新增移动听者、重复冲量、1/8/64/256 听者求值测试，以及真实 ModalSound C++ 基函数与导数交叉核对。[扩展报告](02_PAT/docs/EXTENDED_RESULTS.md)、[移动听者](02_PAT/docs/MOVING_LISTENER.md)、[C++ 验证](02_PAT/docs/MODALSOUND_BASIS.md)。

NeuralSound 已编译 MinkowskiEngine，实际从零训练公开的 **defaultUnet 与 AcousticNet** 各 {vib['epochs']} / {rad['epochs']} 个 epoch。使用 24 个不同长方体，按对象分为 16/4/4；144 张标签通过作者 Bempp 双精度算子与独立线性残差检查。保留最佳/最终权重和训练历史，测试集没有参与 checkpoint 选择。声辐射测试集平均 FFAT 相对 L2 误差 **{rad['test']['mean_transfer_relative_L2']*100:.2f}%**；这是小数据实际误差，不是论文精度。[神经网络报告](03_NeuralSound/docs/TRAINING_RESULTS.md)。

已将预先指定的测试物体 box_21 接入“训练后混合模态求解 → 已训练 AcousticNet → 模态声压 WAV”。六阶模态、三个听者，对照同一 Bempp 辐射参考；三段神经音频相对 L2 误差分别为 **{', '.join(f'{v*100:.2f}%' for v in aud['per_listener_audio_relative_L2'])}**。[音频报告](03_NeuralSound/docs/NEURAL_AUDIO.md)。

## 必须保留的边界与发现

- 完整运行本地流程不等于复现三篇论文的全部实验、测量精度或速度数字。NeuralSound 数据是本地简单几何，未使用完整 ABC 数据和作者预训练权重；公开声辐射网络本身与论文原架构的差别按作者说明保留。
- 官方 `snow` 材料编号没有对应应力分支，实测输出零应力。不能声称雪材料已复现，见 [材料审计](01_PhysGaussian/docs/MATERIAL_AUDIT.md)。
- 原始 NeuralSound 单精度 Bempp + 严格容差出现 GMRES 不收敛；改用同算子双精度、Numba CPU 和 1e-8 相对容差才通过显式残差。原始错误日志保留。
- 本地常面元 BEM 与作者 Bempp 的部分 FFAT 差异较大，所以神经训练改用作者算子全量生成的标签。PAT 的低拟合误差是相对本地 BEM，不证明真实声场已达到同样精度。[交叉核查](03_NeuralSound/docs/BEM_CROSSCHECK.md)。
- 官方 example.obj 默认 GPU LOBPCG 的频率接近参考，但模态向量残差偏大；独立双精度参考通过检查。[官方样例](03_NeuralSound/docs/OFFICIAL_EXAMPLE.md)。
- 没有复现 PAT 原始复杂场景全集、原 FastBEM/Qt 完整工具链、7000 倍速度，未加入碰撞引擎、声传播延迟或 Doppler。没有把三篇不同对象拼接成同一物体的物理一致 3DGS 声画系统。
- 本机为 RTX 2050 4GB。性能记录包含审计/CPU 编译等额外工作；不作为公平论文基准。没有主观试听结论。

## 文件入口和复跑

- [PhysGaussian 说明](01_PhysGaussian/docs/REPRODUCTION.md)
- [PAT 说明](02_PAT/docs/REPRODUCTION.md)
- [NeuralSound 说明](03_NeuralSound/docs/REPRODUCTION.md)
- [环境与命令](复跑与环境说明.md)
- [交付验证记录](交付验证记录.md)、[扩展产物验证](扩展产物验证记录.md)
- [全过程执行记录](继续复现执行记录.md)

输入来源、commit、失败日志、必要适配和数值指标分别在各项目 `docs/` 与 `logs/`；上游源码跟踪文件保持未修改。哈希清单在每个 `docs/artifact-manifest.json`。这份清单用于追溯已保存快照。
''')
    write('01_PhysGaussian/docs/RECONSTRUCTION.md', f'''
# Ficus 原始图像重建训练

真实执行上游 3DGS train.py 30,000 步、render.py 和原 SSIM/PSNR/LPIPS 指标函数。800×800、白背景，100 train / 200 test，`--eval`；val 100 张也已下载但未用于测试指标。输入来自固定 revision 的公开 NeRF synthetic 镜像；镜像出处及每文件哈希见 [数据来源](ficus-dataset-provenance.json)。这不等于已核实作者 Drive 压缩包逐字节相同。

测试平均 PSNR {means['PSNR']:.6f} dB、SSIM {means['SSIM']:.6f}、LPIPS-VGG {means['LPIPS']:.6f}。模型训练使用原优化参数，图像放 CPU 节约显存；评估逐图读取，保留原指标实现。LPIPS/VGG 权重来源有单独哈希记录。

- [四组测试视图对照](../outputs/ficus_reconstruction/heldout_comparison.jpg)
- [完整训练与评估指标](reconstruction-metrics.json)
- [逐图结果](../outputs/ficus_reconstruction/evaluation.json)
- 模型：`outputs/ficus_reconstruction/point_cloud/iteration_30000/point_cloud.ply`
- 训练/渲染/指标日志：`logs/ficus-reconstruction-*.log`

执行 `./run_reconstruction.ps1`；断点和阶段参数见同名 code 脚本。作者发布的 PhysGaussian Ficus `cfg_args` 使用 eval=False，不能用它声称独立测试泛化；本次新训练严格区分测试集。单一 Ficus 的指标也不是全部 3DGS 或 PhysGaussian 论文基准复现。
''')
    write('03_NeuralSound/docs/TRAINING_RESULTS.md', f'''
# 公开神经网络实际训练结果

生成时间：{stamp}。采用 [预先记录的本地协议](LOCAL_TRAINING_PROTOCOL.md)，原网络源码不修改。实际权重、每轮损失和测试产物位于 `outputs/vibration_training` 与 `outputs/radiation_training`。

## 振动与混合求解

defaultUnet(24,48,linear=True)，{vib['epochs']} 轮。初始验证 loss {vib['initial_validation_loss']:.8g}，最佳验证 loss {vib['best_validation_loss']:.8g}；验证改善标记 {vib['validation_improved']}。图矩阵乘法与组装 FEM 的 K/M 相对误差分别为 {vib['graph_A_relative_error']:.3g} / {vib['graph_B_relative_error']:.3g}。测试物体比较随机、未训练网络、已训练网络三种初始化，随后均使用公开 LOBPCG 双精度精修。完整误差、迭代轨迹和单次用时见 [指标](vibration-training-metrics.json)，[学习曲线](../outputs/vibration_training/learning_curve.png)。

训练是单精度原始损失；严格最终求解采用双精度、最多 2000 步和 1e-10 内部容差。没有把数值精修后的准确性全部归因于网络，也没有从一次小实验推断论文加速。重根不逐元素比较特征向量。

## 声辐射

完整公开 AcousticNet(23)，{rad['parameters']:,} 个参数，优化器 {rad['optimizer']}，batch {rad['batch_size']}，{rad['epochs']} 轮。96/24/24 张 train/val/test FFAT，按几何划分。作者代码中 EncoderSmall 实际也构造 ResNet34，保持该结构。

初始验证 loss {rad['initial_validation_loss']:.8g}，最佳 {rad['best_validation_loss']:.8g}，改善标记 {rad['validation_improved']}。测试平均幅值恢复后 FFAT 相对 L2 为 **{rad['test']['mean_transfer_relative_L2']*100:.3f}%**。测试图、归一化图形误差、幅值对数误差和逐样本传递误差都保留：[指标](radiation-training-metrics.json)、[曲线](../outputs/radiation_training/learning_curve.png)、[测试图](../outputs/radiation_training/test_maps.png)。

CPU Adam 若启用，只把优化器状态和更新移至 CPU，保持公开网络及公式；12 步与 torch Adam 的数值对照结果记录在指标内。checkpoint 包含优化器、调度器、随机状态；不能承诺稀疏 GPU 操作跨机器逐比特一致。

## 不能据此宣称的结果

训练完成不等于达到论文精度。24 个简单长方体远小于 ABC 数据，物体数和频率分布都有限；最佳模型只由验证集选择，测试误差如实保留。没有公开匹配预训练权重的查找记录见 [基线审计](BASELINE_REPRODUCTION.md)，没有证明权重在任何地方都不存在。原始数据生成的单精度失败及标签改动见 [BEM 核查](BEM_CROSSCHECK.md)。
''')
    write('03_NeuralSound/docs/NEURAL_AUDIO.md', f'''
# 训练网络到音频的本地完整链路

对象在训练前固定为独立测试集 box_21。输入来自实际训练后 defaultUnet 初始化加 LOBPCG 精修，不是用稠密参考模态替代网络流程；随后调用实际训练的 AcousticNet 权重，输出六张远场幅值 FFAT 并合成三个听者的声压 WAV。

材料为受控的 0.01 倍 Ceramic 刚度：E=7.2e8 Pa、ρ=2700、ν=0.19；不是测量真实陶瓷。频率为 {', '.join(f'{x:.2f}' for x in aud['frequencies_Hz'])} Hz。模态先做物理质量归一化；最大残差 {max(aud['modal_relative_residuals']):.3g}。原 Bempp 双精度算子作为相同输入参考，六次 GMRES 均检查返回码与真实残差。

逐模态 FFAT 相对 L2：{', '.join(f'{v*100:.2f}%' for v in aud['per_mode_ffat_relative_L2'])}。原始负预测比例 {aud['negative_prediction_fraction']*100:.3f}%；仅在音频合成时将负幅值截至零，FFAT 误差按未截断预测报告。三位听者音频相对 L2：{', '.join(f'{v*100:.2f}%' for v in aud['per_listener_audio_relative_L2'])}。

1e-4 N·s 固定方向冲量，距离 0.3 m，Rayleigh α=6、β=1e-7；48 kHz / 3 秒 / PCM16。参考与网络音频共用同一播放增益，原始 Pa 数据和增益另存 raw.npz。末端仅加 20 ms 淡出。

- [波形与 FFAT 图](../outputs/neural_audio/neural_audio.png)
- [全部数值与权重哈希](neural-audio-metrics.json)
- 听者 1：[BEM](../outputs/neural_audio/bem_listener_1.wav) / [神经](../outputs/neural_audio/neural_listener_1.wav)
- 听者 2：[BEM](../outputs/neural_audio/bem_listener_2.wav) / [神经](../outputs/neural_audio/neural_listener_2.wav)
- 听者 3：[BEM](../outputs/neural_audio/bem_listener_3.wav) / [神经](../outputs/neural_audio/neural_listener_3.wav)

这里完成的是本地受控链路，不是论文全数据集精度。采用幅值近似，没有相位、传播延迟、Doppler、接触力求解或碰撞引擎；也没有主观听感评价。运行命令 `./run_numerical.ps1 -Task audio`，需先生成两个已训练网络和混合模态产物。
''')
    write('01_PhysGaussian/docs/REPRODUCTION.md', '''
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
''')
    write('03_NeuralSound/docs/REPRODUCTION.md', '''
# NeuralSound 当前复现记录

已实际运行公开 defaultUnet 与 AcousticNet 的本地训练、独立几何测试及模态到声压音频链路。原仓库提交 `b18e81b1e3dba7e963b09a7d9a45b584707d805f`，跟踪源码保持未修改。不能将本地 24 个长方体训练称为 ABC 全数据或作者预训练性能。

- [训练协议](LOCAL_TRAINING_PROTOCOL.md)、[实际训练与测试结果](TRAINING_RESULTS.md)
- [训练网络到音频](NEURAL_AUDIO.md)
- [作者网格 CUDA 体素化与 FEM/LOBPCG](OFFICIAL_EXAMPLE.md)
- [作者 Bempp 算子交叉核查](BEM_CROSSCHECK.md)、[144 张标签的求解审计](official-labels-dataset.json)
- [基础 FEM 数值验证](RESULTS.md)

实际环境是 WSL Ubuntu1 `/opt/3dgs-runtime/envs/neuralsound` 的独立 Conda，Python 3.9、PyTorch 2.0+cu118、CUDA 11.8、MinkowskiEngine、torch-scatter、Bempp-cl 0.2.4、PyCUDA 2022.2.2。MinkowskiEngine 源码提交 `02fc608bea4c0549b0a7b00ca1bf15dee4a0b228`，在 Linux 磁盘上单任务编译。NumPy 旧别名、整值索引转换、Numba CPU/双精度算子及 CPU Adam 等适配均明确记录，原训练网络不替换为玩具代理。

重跑见 [统一环境与命令](../../复跑与环境说明.md)，各个 run_neural/run_numerical 入口与 code 脚本保存实际参数。训练权重、最佳选择过程、测试误差、随机状态及源文件哈希均可查。早期权重资源核查和 Windows FEM 环境见 [归档记录](BASELINE_REPRODUCTION.md)；其中“尚未训练”只代表早期状态。

默认单精度传统求解存在真实精度问题，未删除失败证据；声辐射误差如实报告。未复现完整 ABC 泛化、论文速度、全刚体接触/碰撞系统，也未取得与公开架构匹配的作者预训练权重。
''')
    write('README.md', '''
# 三篇论文复现

先读 [复现总报告](复现总报告.md)，再按项目查看视频、音频、训练指标和重跑命令。

- [PhysGaussian](01_PhysGaussian/README.md)：官方场景模拟与 SH 渲染、3DGS 外观重建、材料和数值验证。
- [PAT](02_PAT/README.md)：BEM、多极子自适应拟合、移动听者与音频、ModalSound C++ 核验证。
- [NeuralSound](03_NeuralSound/README.md)：实际公开网络训练、独立测试、作者数值模块和神经音频。

[环境与复跑](复跑与环境说明.md) · [文件检查](交付验证记录.md) · [扩展产物检查](扩展产物验证记录.md) · [过程记录](继续复现执行记录.md)

完整本地链路不等于论文全部数据和性能复现；实际精度、适配及未完成原始基准在报告中明确区分。原上游代码与失败日志保留。
''')
    write('01_PhysGaussian/README.md', '''
# PhysGaussian

已完成官方完整场景模拟与透视 SH CUDA 渲染、Ficus 30,000 步外观训练和独立视图指标，并保留基础 MPM 数值与材料核验证。

- [复现记录](docs/REPRODUCTION.md)
- [官方场景视频与状态审计](docs/OFFICIAL_SCENES.md)
- [原始图像重建与测试](docs/RECONSTRUCTION.md)
- [材料检查](docs/MATERIAL_AUDIT.md)

入口 `run_scenes.ps1`、`run_reconstruction.ps1`；基线入口 `run.ps1`、`run_ficus.ps1`。完整环境与命令见根目录 [说明](../复跑与环境说明.md)。
''')
    write('03_NeuralSound/README.md', '''
# NeuralSound

已实际从零训练公开 defaultUnet 与 AcousticNet，完成本地独立几何测试及六阶模态到声压 WAV 的链路。使用小规模程序化数据，不等同于论文 ABC 数据精度。

- [复现记录](docs/REPRODUCTION.md)
- [实际训练和测试](docs/TRAINING_RESULTS.md)
- [神经音频及 BEM 对照](docs/NEURAL_AUDIO.md)
- [官方网格体素化与模态求解](docs/OFFICIAL_EXAMPLE.md)
- [BEM 标签核查](docs/BEM_CROSSCHECK.md)

训练入口 `run_neural.ps1 -Task vibration|radiation`，数值/音频入口 `run_numerical.ps1 -Task example|bem|labels|audio`，基础 FEM 为 `run.ps1`。详见根目录 [环境与复跑](../复跑与环境说明.md)。
''')
    # Include the later executed extensions from their saved measurements.
    fem = read('02_PAT/docs/modalsound-fem-metrics.json')
    benchmark = read('03_NeuralSound/docs/vibration-benchmark.json')
    hybrid = read('03_NeuralSound/docs/example-hybrid-ood-metrics.json')
    hybrid_extended = read('03_NeuralSound/docs/example-hybrid-ood-extended-metrics.json')
    trained_ood = next(r for r in hybrid_extended['records'] if r['initialization']=='trained_network')
    acoustic = read('03_NeuralSound/docs/example-acoustic-ood-metrics.json')
    assert fem['all_checks_passed'] and benchmark['all_checks_passed']
    assert hybrid['execution_completed'] and acoustic['execution_completed']
    def append(rel, content):
        path = ROOT / rel
        path.write_text(path.read_text(encoding='utf-8')+'\n'+content.strip()+'\n', encoding='utf-8')
    extra = f'''
## 补充完成的原代码实验

- ModalSound 原始 C++ 四面体质量矩阵、StVK 刚度矩阵实际编译运行；独立 BᵀDB/一致质量、六个刚体模态、固定端模态和刚度缩放均通过检查。[C++ FEM 报告](02_PAT/docs/MODALSOUND_FEM.md)。
- 振动求解计时包含网络与 SVQB 初始化；每配置预热一次、测量三次，共四个测试物体和三种初始化。[完整计算阶段计时](03_NeuralSound/docs/VIBRATION_BENCHMARK.md)。
- 作者原始 example.obj 的 3863 体素、17,898 自由度输入实际训练后的振动网络，随后用原 LOBPCG 稀疏双精度精修。三种初始化均执行，收敛与误差逐项保存。[原网格混合求解](03_NeuralSound/docs/EXAMPLE_HYBRID_OOD.md)。
- 原网格初次 2000 步均未达标；独立增加至 10000 步后，随机和未训练网络初始化通过，但已训练网络最大残差仍为 **{trained_ood['max_relative_residual']:.6g}**，未通过。小几何上的训练改善不能外推到此网格，不能声称神经振动普遍加速。[保留失败的收敛诊断](03_NeuralSound/docs/EXAMPLE_HYBRID_OOD_EXTENDED.md)。
- 同一作者原网格预先指定的两个模态，使用独立 FEM 与官方 Bempp 生成参考；冻结声辐射网络的平均 FFAT 相对 L2 为 **{acoustic['test']['mean_transfer_relative_L2']*100:.3f}%**。这是超出长方体训练族的真实泛化检查。[原网格声辐射](03_NeuralSound/docs/EXAMPLE_ACOUSTIC_OOD.md)。
- 新训练 Ficus 的 30,000 步 PLY 已重新进入完整五秒物理模拟，模型哈希与训练输出核对；125 帧原 SH 渲染见 [视频](01_PhysGaussian/outputs/ficus_reconstructed_full/output.mp4)。
'''
    append('复现总报告.md', extra)
    neural_links = '''
## 补充实验

- [包含网络初始化成本的三次重复计时](VIBRATION_BENCHMARK.md)
- [作者原始网格的神经振动混合求解](EXAMPLE_HYBRID_OOD.md)
- [保留原失败结果的更长迭代收敛诊断](EXAMPLE_HYBRID_OOD_EXTENDED.md)
- [作者原始网格的冻结声辐射网络测试](EXAMPLE_ACOUSTIC_OOD.md)
- [CPU Adam 存储、数值一致性与性能记录](CPU_ADAM_PROFILE.md)
- [声辐射预测未达标：平均、中位数及逐物体误差](RADIATION_ACCURACY.md)
- [全部24张测试图：物理幅值对照与原始数组](ALL_TEST_PREDICTIONS.md)
- [本地特征编码与作者数据类的 12 样本对照](acoustic-feature-contract.json)
- [四个训练检查点实际读回与恢复状态验收](checkpoint-audit.json)
- [保存的12组振动模态重新装配物理FEM复核](vibration-array-audit.json)

正式声辐射训练采用原 batch 40、CPU 线程 8；96 张训练图每轮随机打乱后 drop_last，每轮两批，使用 80 张。batch 2 是独立资源试验，未用于初始化正式权重。CPU master Adam 另有 18 次更新（含第 9 次保存恢复）的独立数值核对；正式训练内也执行短对照。随机数状态的实际调用顺序见训练协议。
'''
    append('03_NeuralSound/docs/TRAINING_RESULTS.md', neural_links)
    append('03_NeuralSound/docs/REPRODUCTION.md', neural_links)
    # All links in this section refer to files in the local docs directory.
    append('03_NeuralSound/README.md', neural_links.split('正式声辐射训练')[0].replace('](', '](docs/'))
    append('01_PhysGaussian/docs/RECONSTRUCTION.md', '''
## 重新接入物理模拟

已将本次独立训练的最终 PLY 用于相同 Ficus 配置的完整五秒模拟及 125 帧 SH 渲染。入口 `run_reconstructed_simulation.ps1`；[视频](../outputs/ficus_reconstructed_full/output.mp4)、[运行指标与模型哈希](../outputs/ficus_reconstructed_full/metrics.json)。与作者发布模型的结果分别保存。
''')
    append('复现总报告.md', '''
## 完成性复核补充

- [逐项最终验收](最终验收报告.md)：对原计划、三篇论文核心方法和实际交付逐项标明完成、失败及资源边界。
- [高斯输运独立检查](01_PhysGaussian/docs/GAUSSIAN_TRANSPORT.md)：实际 CUDA 协方差、极旋转、SH 以及增量 g2p 收敛。
- [可选各向异性正则完整实验](01_PhysGaussian/docs/ANISOTROPY_RESULTS.md)：另一组30,000步训练、200测试视图和125帧模拟，保留原训练结果。
- [SH 坐标系问题与修复](01_PhysGaussian/docs/SH_FRAME_AUDIT.md)、[三场景完整对照](01_PhysGaussian/docs/SH_CORRECTED_SCENES.md)：原代码未改，修复版独立保存。
- [ModalSound 原边界积分、多极子后处理](02_PAT/docs/MODALSOUND_TRANSFER.md)：九组解析边界迹、原 C++ 运行与二进制矩系数回读；没有冒充 FastBEM 求解。
- [NeuralSound 正文优化器参数对照](03_NeuralSound/docs/PAPER_SCHEDULE_RESULTS.md)：另训两网络各100轮，保持原失败结果；仍非完整ABC协议。
- [原计划 A1 的数组和音频独立验收](reproduction/traditional/ACCEPTANCE.md)。
''')
    for target,prefix in (('01_PhysGaussian/docs/REPRODUCTION.md',''),('01_PhysGaussian/README.md','docs/')):
        append(target,'\n## 完成性复核\n\n'+'\n'.join(f'- [{label}]({prefix}{file})' for label,file in (
            ('高斯协方差、旋转和增量输运','GAUSSIAN_TRANSPORT.md'),('各向异性正则完整实验','ANISOTROPY_RESULTS.md'),
            ('SH 坐标系独立审计','SH_FRAME_AUDIT.md'),('SH 修复三场景同状态对照','SH_CORRECTED_SCENES.md'))))
    for target,prefix in (('03_NeuralSound/docs/REPRODUCTION.md',''),('03_NeuralSound/README.md','docs/')):
        append(target,f'\n[正文优化器参数对照结果]({prefix}PAPER_SCHEDULE_RESULTS.md)：两网络另训100轮、全部预测与检查点验收；不覆盖或替代原发布参数实验。')
    append('README.md','[逐项最终验收报告](最终验收报告.md) · [基础声音验收](reproduction/traditional/ACCEPTANCE.md)')
    print('Reports generated from completed metrics:', stamp)


if __name__ == '__main__':
    main()
