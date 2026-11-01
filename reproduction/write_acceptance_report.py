"""Requirement-by-requirement acceptance based on completed, audited artifacts."""
import json
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8-sig'))


def main():
    audit=read('reproduction/extended-artifact-audit.json')
    assert audit['passed'] and len(audit['checks'])>=31,'Run the expanded verifier before acceptance.'
    scenes=read('01_PhysGaussian/docs/official-scenes-verified.json');assert len(scenes)==11
    an=read('01_PhysGaussian/docs/anisotropy-metrics.json');assert an['all_checks_passed']
    rad=read('03_NeuralSound/docs/radiation-paper-schedule-metrics.json');assert rad['training_completed']
    oldrad=read('03_NeuralSound/docs/radiation-training-metrics.json')
    checkpoint=read('03_NeuralSound/docs/paper-schedule-checkpoint-audit.json');assert checkpoint['passed']
    stamp=datetime.now().astimezone().isoformat(timespec='minutes')
    report=f'''# 最终逐项验收报告

生成时间：{stamp}。验收依据为原 [REPRODUCTION_PLAN.md](REPRODUCTION_PLAN.md)、三篇本地论文及用户追加的“按三篇分目录、Conda优先、完成可行内容、记录到文档、不得擅自改项目外文件”。论文页级核查和来源哈希见 [原文审计](reproduction/audit/paper_scope/sources.json)。旧报告中的阶段状态保留，不作为当前结论。

## 验收结论

当前约定范围内、使用已取得资源可完成的模块实验和完整本地链路已实际执行并核对产物。不是三篇论文全部原始数据、图表、实测精度和性能的完整复现。不能把公开实现的缺失、网络预测失败或未获得的原始数据写成成功。

- PhysGaussian：六个公开场景原配置；两次独立 Ficus 30,000 步训练（基线、可选各向异性正则），各200测试视图；两模型分别完整模拟；非单位预旋转的三个场景另跑 SH 修复对照。合计 **{len(scenes)} 段完整模拟、{sum(r['frames'] for r in scenes):,} 帧**，均有逐帧检查和最终全粒子状态。
- PAT：本地 Helmholtz BEM → 单层/多层多极子拟合 → 独立空间点验证 → 冲量/移动听者 WAV；真实 ModalSound C++ 基函数、FEM、边界积分、多极子矩生成/保存/求值都已运行。
- NeuralSound：完整公开网络两组配置实际训练，原发布参数振动200轮/辐射100轮，正文优化器参数另各100轮；全部测试、冻结模型原网格测试、音频和精修对照均有结果。正文配置 FFAT 平均相对L2 **{rad['test']['mean_transfer_relative_L2']*100:.3f}%**，原发布配置 **{oldrad['test']['mean_transfer_relative_L2']*100:.3f}%**，保持两者独立记录。

最终独立产物审计包含 **{len(audit['checks'])} 项检查**，见 [扩展产物验收](扩展产物验证记录.md)。文件、代码语法、文档链接、环境和哈希另由 [交付文件验收](交付验证记录.md) 检查；最新运行时间应以相应文件为准。

## 原计划逐项验收

1. **A0：原代码、版本、许可证、声学系数来源。已完成核查。** ModalSound 是2016教学代码，不能冒充PAT 2006原完整实现。固定commit、许可证和构建路径保留。真实C++后处理已补跑，但使用明确标注的解析边界迹，不宣称获得FastBEM求解器。证据：[PAT复现说明](02_PAT/docs/REPRODUCTION.md)、[原C++后处理](02_PAT/docs/MODALSOUND_TRANSFER.md)。
2. **A1：矩阵、模态、冲量、阻尼、对照、WAV。全部通过本地原理实验验收。** 固定左端24质量块系统；基线、刚度×4、质量×4、阻尼×4、改变敲击点共五组。独立重新装配矩阵、积分物理坐标，与原始数组和全部音频逐样本复核。共同播放增益、原始幅值、低于奈奎斯特的截断均保存。是振动可听化，不是声压。证据：[A1验收](reproduction/traditional/ACCEPTANCE.md)、[原参数与结果](reproduction/traditional/outputs/RESULTS.zh-CN.md)。
3. **A2：声辐射和听者方向。已完成本地完整声学链路。** 三听者、移动听者、重复冲量、1/8/64/256听者求值均已执行，远超简单单极子示意；输入仍为本地小梁。证据：[PAT基础](02_PAT/docs/RESULTS.md)、[扩展](02_PAT/docs/EXTENDED_RESULTS.md)、[移动听者](02_PAT/docs/MOVING_LISTENER.md)。
4. **B0：官方资源、权重和环境门槛。已核查并实测解决依赖。** 仓库、项目页、Releases/Issues快照和失败请求都保存。未找到匹配的公开预训练权重，所以从头训练公开网络；没有用随机权重冒充预训练推理。WSL GPU、MinkowskiEngine、PyCUDA、Bempp已实际使用，4GB显存可行性由实验确认。证据：[原始资源核查](03_NeuralSound/docs/BASELINE_REPRODUCTION.md)、[实际环境](复跑与环境说明.md)。
5. **B1：有意义的推理、数值参考及音频。已完成本地学习流程，准确性未全部通过。** 保存真实训练权重、归一化、输入、全部24张FFAT、原始数组及误差；混合振动保留随机/未训练/已训练三种初始化，近重根不直接逐元素比向量；六段神经/BEM音频来自实际网络链路。证据：[训练](03_NeuralSound/docs/TRAINING_RESULTS.md)、[全预测](03_NeuralSound/docs/ALL_TEST_PREDICTIONS.md)、[音频](03_NeuralSound/docs/NEURAL_AUDIO.md)。
6. **B2：传统模块与小数据范围。完成官方数值模块并扩展实际网络训练。** 没有下载完整ABC；没有用玩具代理替代公开网络。对完整原论文数据和公开架构差异继续保留限制。证据：[官方FEM](03_NeuralSound/docs/RESULTS.md)、[官方网格](03_NeuralSound/docs/OFFICIAL_EXAMPLE.md)、[本地协议](03_NeuralSound/docs/LOCAL_TRAINING_PROTOCOL.md)。
7. **执行与交接。已按三篇分文件夹，使用隔离Conda，GPU重型阶段串行。** 日志、源码差异说明、输入/权重来源、运行入口、负结果均入文档。未关闭用户应用、未改驱动；后续续跑只读使用既有外部Conda，新增依赖/缓存/检查点留在项目内。证据：[环境复跑](复跑与环境说明.md)、[全过程](继续复现执行记录.md)、[状态](STATUS.md)。

## PhysGaussian 论文方法覆盖

1. **视觉重建与高斯输入。实际原3DGS训练和光栅器。** 原Ficus800×800、100训练视图与200测试视图，30,000步基线PSNR34.847324dB、SSIM0.987180645、LPIPS0.011693542；原作者eval=False模型不用于独立测试声明。[重建证据](01_PhysGaussian/docs/RECONSTRUCTION.md)。
2. **连续体/MPM与材料。实际未修改Warp核及完整配置。** 基础梁刚度趋势、质量守恒、数值有限性、材料本构检查；六个发布场景全长运行。场景内填充、预处理、边界/施力均走原代码配置；不是用自建弹簧替代MPM。[基础结果](01_PhysGaussian/docs/RESULTS.md)、[材料审计](01_PhysGaussian/docs/MATERIAL_AUDIT.md)、[场景和逐帧状态](01_PhysGaussian/docs/OFFICIAL_SCENES.md)。
3. **§3.4–3.6 / 式(8)–(10)。独立验证96组协方差、极旋转和SH，原g2p增量分支实际执行。** 与矩阵公式、行列式/高斯指数不变量、SciPy极分解、矩阵指数比对；减半步长误差比约2。[输运报告](01_PhysGaussian/docs/GAUSSIAN_TRANSPORT.md)。
4. **§3.8 / 式(12)。完整本地各向异性正则对照。** 预定r=5、λ=0.01，独立已知值/梯度检查，另训30,000步并200视图评估、125帧模拟。正则化模型平均轴比{an['axis_ratios']['regularized']['mean']:.6g}，基线{an['axis_ratios']['baseline']['mean']:.6g}。这些参数和Ficus不是原图8凳子设置；不能宣称复制图8原始定量结果。[协议与实测](01_PhysGaussian/docs/ANISOTROPY_RESULTS.md)。
5. **发现并保留SH坐标系错误。** 原非单位预旋转不变量失败，外部QᵀR⁻¹Q适配后通过；bread/plane/vasedeck完整重跑，每帧同状态双渲染比较。旧视频保留，图像差异不是动态真值误差。[失败与修复](01_PhysGaussian/docs/SH_FRAME_AUDIT.md)、[完整对照](01_PhysGaussian/docs/SH_CORRECTED_SCENES.md)。
6. **未实现/未证实。** snow编号缺少原应力分支，实测零应力，不将自创雪模型冒充作者实现。未取得全论文场景的原始拍摄/训练数据、动态真实图像和匹配配置；未验证全材质实验测量、论文全部速度表。已有六场景结果不等于原论文全部实验。

## PAT 论文方法覆盖

1. **§3：模态振动与声学预计算。** 官方FEM物理模态输入，本地Neumann/Helmholtz BEM与球解析检查，保留首次网格单调性失败和跨实现差异。原文允许标准声学求解器；本地方法不冒充Neo Acoustics。[方法和失败](02_PAT/docs/REPRODUCTION.md)、[Bempp交叉核查](03_NeuralSound/docs/BEM_CROSSCHECK.md)。
2. **§4.1–4.2：多极子与加权拟合。** 球Hankel/球谐基、面积加权、截断SVD、独立空间点误差；原C++基函数及导数另与SciPy对照。[C++基函数](02_PAT/docs/MODALSOUND_BASIS.md)。
3. **§4.3：源位置选择与多层拟合。** 距离场/marching cubes偏移面、三层随机候选选择、九项展开、12模态1792面片；拟合点和独立验证点分开，保存单层/多层比较。[扩展算法和指标](02_PAT/docs/EXTENDED_RESULTS.md)。
4. **运行时声音。** 三固定听者与移动听者，冲量激发与阻尼，共同播放增益；音频来自声学传递而非只有衰减正弦。忽略相位的幅值近似按论文范围记录；无传播延迟、Doppler或完整接触引擎。[移动听者结果](02_PAT/docs/MOVING_LISTENER.md)。
5. **公开教学代码的可行部分。** 真实C++四面体质量/刚度组装；原边界积分、多极子矩、二进制保存和求值九组实际执行。二进制矩独立回读且重新求值。[FEM](02_PAT/docs/MODALSOUND_FEM.md)、[后处理](02_PAT/docs/MODALSOUND_TRANSFER.md)。
6. **未完成的原始基准。** 没有原论文复杂模型/全模态/原始参考声场和Neo Acoustics；教学仓库不含完整FastBEM求解资源，解析边界迹不能填补这个缺口。Qt界面非数值必需，未把未构建GUI描述成核心代码未跑。未验证7000倍加速或高频/内共振稳健性；不以低拟合误差掩盖BEM离散偏差。

## NeuralSound 论文方法覆盖

1. **体素化/FEM/传统解。** 原example.obj实际GPU体素化和原FEM，独立双精度参考、刚体模态、特征残差和缩放律；默认GPU LOBPCG向量残差失败保留。[官方网格](03_NeuralSound/docs/OFFICIAL_EXAMPLE.md)。
2. **振动网络/混合求解。** 完整公开defaultUnet训练，原Rayleigh–Ritz与LOBPCG精修；两种训练配置分别测固定四测试几何，12种初始化配置；额外计时包含网络/SVQB初始化、预热与重复测量。[振动结果](03_NeuralSound/docs/VIBRATION_RESULTS.md)、[完整计时](03_NeuralSound/docs/VIBRATION_BENCHMARK.md)。
3. **声辐射训练和FFAT。** 24个不同程序化几何、16/4/4隔离划分、144张原Bempp算子标签；完整311,180,810参数AcousticNet，CPU Adam仅转移状态更新存储。原公开代码参数与论文正文参数都实际执行；全部测试图、幅值误差和检查点均保存。[发布参数结果](03_NeuralSound/docs/TRAINING_RESULTS.md)、[正文参数对照](03_NeuralSound/docs/PAPER_SCHEDULE_RESULTS.md)。
4. **正文§6.2差异已明确。** 两网络100轮、lr1e-4每20轮减半，辐射batch16已作为独立对照执行。仍是本地24几何、6个展开模态、每轮全部16训练几何；没有执行论文100K ABC、4:1:1划分、5随机模态/随机材质和振动每轮1/20子集。公开声辐射结构不同于论文原网络，不能靠匹配优化器消除结构和数据差异。
5. **音频与原网格泛化。** 六阶混合模态→真实训练AcousticNet→三听者WAV并对照Bempp；原example.obj两个声辐射模态、三种混合初始化及10,000步长预算诊断均执行。已训练振动在原网格残差4.959×10⁻⁴仍不达标，声辐射平均误差99.806%；原神经音频误差263.625%/136.371%/98.290%保留。[音频](03_NeuralSound/docs/NEURAL_AUDIO.md)、[原网格长迭代](03_NeuralSound/docs/EXAMPLE_HYBRID_OOD_EXTENDED.md)、[原网格声辐射](03_NeuralSound/docs/EXAMPLE_ACOUSTIC_OOD.md)。
6. **未达论文结果。** 目前的学习精度与泛化不能验收为论文复现成功；没有匹配作者预训练权重、原100K数据协议或相同硬件/求解条件，不宣称论文准确性或加速比。没有通过重新划分测试集、挑图或隐去失败来“达标”。

## 文档、来源与复跑验收

- 三篇各有 README、paper、code、inputs、outputs、docs、logs，原上游commit与许可记录保留。外部包装器/本地重写和作者模块明确区分。
- 旧2,825项manifest逐字节核验完成，原数据/权重/结果未改；完整旧清单保存在 [旧快照](reproduction/audit/previous-manifests-snapshot.json)，本轮新产物由最终三项目manifest记录。旧快照比对是历史检查，不把随后有意编辑的适配器/文档误报成未修改。
- 完整新旧训练状态均实际读回，检查模型/优化器张量有限、epoch、scheduler和RNG；项目内新检查点保留。输入、权重、论文、上游文件和科学输出有来源或哈希。
- [环境与命令](复跑与环境说明.md) 提供分阶段执行和只验证产物入口；汇总run_full.ps1经过语法检查，**未再次从头执行整个汇总脚本**，实际执行的是对应阶段命令。
- 可视化图像由保存结果生成并实际检查，逐文件观察见 [本轮视觉检查记录](reproduction/audit/scope-visual-review.md)；WAV做PCM与数值检查，没有虚构主观试听、音质评测或用户实验。
- [PROGRESS.md](PROGRESS.md) 和 [当前状态](STATUS.md) 为索引；[执行记录](继续复现执行记录.md) 保留时间、修复、原失败和实际命令。

## 为什么在这里结束本次复现

计划要求的原理验证、可取得的作者模块、受控本地完整流程及上述补充实验已有可查结果；剩余项目需要原论文未取得的数据/权重/商业求解资源或属于新的研究任务。完整ABC下载不属于原计划本地路线；不能为追求“全部成功”无限改变训练集、方法或验收阈值。若未来提供原资源，可以按当前隔离入口扩展原始基准。

把3DGS变形物体自动变成同一几何/材料/质量的声学FEM对象，统一接触力、振动和声辐射，属于用户后续研究目标，不是三篇任一篇已经提供的一键系统。本次没有用不同物体的图片和声音拼接冒充这一目标已经实现。
'''
    (ROOT/'最终验收报告.md').write_text(report,encoding='utf-8')
    (ROOT/'reproduction/audit/final-acceptance.json').write_text(json.dumps(dict(
        generated=stamp,local_feasible_scope_completed=True,full_paper_benchmarks_reproduced=False,
        scene_runs=len(scenes),rendered_frames=sum(r['frames'] for r in scenes),extended_check_count=len(audit['checks']),
        evidence_report='最终验收报告.md',negative_results_preserved=True),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Requirement-by-requirement acceptance report generated:',stamp)


if __name__=='__main__':main()
