"""Assemble final assessment from this verification's evidence, never old status prose."""
import json
from common import AUDIT,save,stamp
def get(path):return json.loads((AUDIT/path).read_text(encoding='utf-8'))
def fmt(x):return f'{x:.8g}'
def main():
    fresh=get('evaluations/fresh_30000/metrics.json');old=get('evaluations/existing_baseline/metrics.json');rerender=get('evaluations/existing_model_rerender/metrics.json')
    trained=get('checks/fresh-trained-model.json');simulation=get('checks/fresh-simulation.json');transport=get('physics/outputs/gaussian_transport/metrics.json');sh=get('physics/outputs/sh_frame_audit/metrics.json')
    material=get('materials_linux/outputs/material_audit/metrics.json');inference=[get('neural/'+tag+'/metrics.json') for tag in ('radiation_training','radiation_paper_schedule')]
    vibration=get('neural/vibration-fresh-solves.json');checkpoints=get('checks/checkpoints.json');native=get('checks/native-metrics.json');protected=get('original-files-after.json')
    builds=get('cuda-build-results.json');rebuilt=get('checks/rebuilt-render-comparison.json');oldrender=get('checks/existing-model-rerender.json');labels=get('checks/fresh-bem-labels.json')
    chain=get('checks/fresh-fem-pat-chain.json');basis=get('checks/fem-basis-audio-invariance.json');traditional=get('checks/traditional.json');aniso=get('checks/anisotropy.json')
    assert protected['passed'] and len(checkpoints)==8 and len(vibration)==8
    items=[]
    def add(code,status,title,detail,commands,paths):items.append(dict(id=code,status=status,title=title,detail=detail,commands=commands,evidence=paths))
    add('V01','通过','源码、目录与数据内容检查','三个论文目录、作者源码与本地适配器可区分。记录三个提交号；Windows Git 跟踪文件干净。NeuralSound 的 51 个跟踪文件另与 HEAD 逐字节核对：43 个仅 CRLF/LF 差异，规范化换行后零实质差异。Ficus 403 个来源清单文件匹配，100/200/100 张训练/测试/验证 RGBA 图可解码，训练与测试无相同图像哈希。24 个本地体素几何各不相同，16/4/4 划分无重复。','independent_cpu.py；check_git_lineendings.py；check_manifest_and_metadata.py',['checks/source.json','checks/data.json','checks/git-lineendings.json','checks/manifest-comparison.json'])
    add('V02','通过','现有 Conda 环境的实际运行能力','Windows acoustics 与 physgaussian 的 pip check 通过；Linux physgaussian 与 neuralsound 的 pip check、核心模块导入、CUDA 矩阵运算通过。真实训练、编译和推理进一步检验运行能力。pat-tools 是 GSL/Boost 工具前缀，不包含 Python，其有效性用实际 C++ 编译/链接判断。','check_windows.py；preflight_linux.py；各 env-* 与 windows-*-pip 命令',['environment-windows.json','environment-linux.json','补充环境检查说明.md'])
    add('V03','失败','Windows 环境导出文件的路径记录','01_PhysGaussian/docs/environment.yml、02_PAT/docs/environment.yml、03_NeuralSound/docs/environment.yml 的 name/prefix 含 Unicode 替换字符，记录的中文工作目录已损坏。现有环境可运行不能证明这些导出可原样恢复原路径。本轮没有修复文件，也没有新建环境验证恢复。','check_manifest_and_metadata.py',['checks/environment-export-text.json'])
    add('V04','通过','脚本语法与现有数据文件完整性','本地 Python 适配器 AST 解析、15 个 PowerShell 入口解析和本轮记录的 Bash -n 检查通过；旧清单中 5986 个文件逐字节哈希匹配。这只说明语法/字节完整性，不是算法正确性证明。','independent_cpu.py；check_windows.py；media_and_syntax.py',['checks/source.json','checks/bash-syntax.json','checks/manifest-comparison.json'])
    add('V05','通过','A1 传统模态原理实验的独立数值核验',f'新构造差分关联矩阵 K、使用固定/自由链闭式频率及全波形解析解核对五组实验。最大频率绝对误差 {fmt(max(r["analytic_frequency_error"] for r in traditional["records"]))} Hz；最大波形相对 L2 {fmt(max(r["waveform_relative_L2"] for r in traditional["records"]))}。核对模态残差、质量正交、刚度/质量缩放、冲量、阻尼、频带截断及共同增益 PCM；五段与总拼接 WAV 一致。未把该振动可听化声称为 PAT。','independent_cpu.py；audio_readback.py',['checks/traditional.json','checks/audio-readback.json'])
    add('V06','通过','PAT 相关原 C++ FEM 与边界积分/多极子模块构建','实际用 g++ 编译、链接并执行两个二进制。FEM 对独立 BᵀDB/一致质量参考的误差约 5e-16，检查自由体六刚体模态和固定端/刚度缩放。9 个解析声场案例中，多极子对直接积分误差约 1e-8 或更小；1280 面片对解析场误差约 0.29%。这是 ModalSound 2016 教学代码模块，不是 PAT 2006 全部原始软件。','build_and_test_pat.py；build-pat-fem；build-pat-transfer；rerun-pat-fem；rerun-pat-transfer',['pat-executions.json','pat/outputs/modalsound_fem/metrics.json','pat/outputs/modalsound_transfer/metrics.json'])
    add('V07','通过','本地 FEM→BEM→PAT→WAV 链路从头运行',f'重新计算 24 体素梁的作者 FEM/Lanczos 模态，再输入本地 BEM/PAT 实现，生成六段 WAV；六个 PCM 文件均直接从原始声压/共同增益重算一致。新链路 PAT 对同次 BEM 音频相对 L2 为 {chain["audio_relative_L2"]:.3%}。另一次固定旧模态输入的 BEM→PAT 重跑误差为 1.138%。二者输入模态基不同，不能混为同一数值结果。','fresh_cpu_pipeline_retry_job.py → fresh_cpu_pipeline.py；另 run_pat_isolated.py pipeline',['checks/fresh-fem-pat-chain.json','fresh_cpu_pipeline_retry/fem/metrics.json','fresh_cpu_pipeline_retry/pat/outputs/pat_pipeline/metrics.json','fresh_cpu_pipeline_retry/pat/outputs/pat_pipeline/pressure_audio_raw.npz'])
    add('V08','失败','声学输出对等价 FEM 模态基的不变性',f'同一几何/材料的 K、M 相对差异分别 {fmt(basis["matrix_relative_errors"]["K_N_per_m"])}、0；频率最大相对差异 {fmt(basis["max_frequency_relative_error"])}，重建物理位移相对差异 {fmt(basis["reconstructed_displacement_relative_L2"])}。但原实现 abs(transfer) @ modal_response 的声压相对差异为 {basis["BEM_magnitude_audio_relative_L2"]:.3%}。保留复数传递系数作对照时差异仅 {fmt(basis["complex_transfer_control_relative_L2"])}，支持符号/相位丢弃是原因。该幅值近似沿用论文思路；这里判定的是物理输入相同时的数值不变性失败，不声称听感试验失败或整篇论文公式错误。','compare_fem_modes.py',['checks/fem-basis-audio-invariance.json','fem-basis-audio.log'])
    add('V09','未验证','PAT 网格收敛、完整原论文场景与性能','实际重跑的本地球体 BEM 误差在 80/320/1280 面片分别为 0.105%/2.111%/1.600%，并非单调收敛；梁首模态粗细网格场差约 6.566%。虽线性残差很小，不能据此宣称空间离散误差收敛。未完成论文复杂物体、NeoAcoustics 原流程、薄壳/高频与多层算法基准、7000 倍加速或原论文听感实验。','rerun-pat-pipeline；fresh-fem-pat-chain-retry；论文原文核对',['pat/outputs/pat_pipeline/metrics.json','fresh_cpu_pipeline_retry/pat/outputs/pat_pipeline/metrics.json','papers/02_PAT.txt'])
    add('V10','通过','全新 3DGS 30,000 步训练',f'直接运行固定作者 train.py，从数据集初始点云开始，未加载已训练权重。Ficus 800×800，100 训练/200 测试视图，eval、白背景、CPU 存图。30,000 步完成；新 PLY {trained["particles"]} 个高斯，各字段有限；最终检查点 iteration=30000，递归检查模型及优化器张量有限。','run_3dgs.py → 3dgs-train；post_results.py',['commands/3dgs-train.json','logs/3dgs-train.log','outputs/ficus_fresh_30000/cfg_args','outputs/ficus_fresh_30000/point_cloud/iteration_30000/point_cloud.ply','checks/fresh-trained-model.json'])
    def metricline(m):return ', '.join(k+'='+fmt(m['mean'][k]) for k in ('PSNR','SSIM','LPIPS'))
    add('V11','通过','新模型全部 200 测试视图渲染与独立评估','原 render.py 完成全部 200 张。逐张核对真实测试 RGBA 按对应相机次序白背景合成，GT 量化差不超过 1 字节；独立 NumPy 计算 PNG PSNR，使用作者 SSIM 与 LPIPS-VGG。新训练：'+metricline(fresh)+'。旧保存图重新计算：'+metricline(old)+'。这是本地静态重建指标，不是 PhysGaussian Table 1 的变形场景指标。','3dgs-render；3dgs-evaluate-fresh；3dgs-evaluate-existing',['evaluations/fresh_30000/metrics.json','evaluations/fresh_30000/comparison.jpg','evaluations/existing_baseline/metrics.json'])
    add('V12','通过' if native['passed'] else '失败','未修改作者 metrics.py 全视图入口','本轮另直接尝试原 metrics.py 全视图入口；不能只看退出码，因为作者脚本会捕获异常后返回 0。'+('已生成结果，三项均与独立流式评估在 1e-4 内一致。' if native['passed'] else '未得到通过产物检查的完整结果；具体日志如下。独立流式评估的通过结论仅属于 V11，不用它覆盖此入口的问题。'),'native_metrics_check.py → 3dgs-native-metrics',['checks/native-metrics.json','logs/3dgs-native-metrics.log'])
    add('V13','通过' if all(r['exit_code']==0 for r in builds) else '失败','CUDA 扩展从源码隔离重编译',f'将原 simple-knn 与 diff-gaussian-rasterization 源码复制到验证目录并先核对哈希；build_ext 编译、未安装覆盖原环境。实际 KNN 对照 torch.cdist，随后新编译光栅器渲染同一新模型全部 200 视图。新旧光栅器最大 PNG 字节差 {rebuilt["maximum_byte_difference"]}，完全一致 {rebuilt["exactly_equal_images"]}/200。','build_cuda.py；cuda-build-*；cuda-rebuilt-knn-test；cuda-rebuilt-render',['cuda-build-results.json','checks/rebuilt-render-comparison.json','build/'])
    add('V14','通过','既有 3DGS 模型重新渲染',f'只复制旧模型 PLY/cfg 到验证目录，运行原 render.py 全部 200 视图并重新评估。相对历史保存图最大字节差 {oldrender["max_byte_difference"]}，完全一致 {oldrender["identical_images"]}/200。重渲染指标：'+metricline(rerender)+'。','3dgs-existing-model-rerender；3dgs-evaluate-existing-rerender',['checks/existing-model-rerender.json','evaluations/existing_model_rerender/metrics.json','outputs/ficus_existing_rerender/'])
    add('V15','通过','新训练 3DGS 模型的完整 Ficus 物理模拟',f'将本轮新 PLY 交给原 Ficus 配置与发布的 gs_simulation，保留现有外部低显存适配。重新完成 125 帧，125 张 PNG 与 MP4 逐帧解码数一致；{simulation["particles"]} 个粒子最终原始数组有限，最大位移 {fmt(simulation["max_displacement"])}。只验证运行及内部一致性，没有实物轨迹真值。','physics_isolated.py simulation；post_results.py',['commands/physics-fresh-full.json','physics/outputs/ficus_fresh_full/metrics.json','physics/outputs/ficus_fresh_full/output.mp4','physics/outputs/ficus_fresh_full/verified_contact_sheet.jpg','checks/fresh-simulation.json'])
    add('V16','通过','高斯输运与增量协方差的实际核心测试',f'重新执行 96 个正定协方差/正行列式变形案例，调用原 Warp 核心、极分解、g2p 和 SH。协方差相对 L2 {fmt(transport["checks"]["covariance_relative_L2"])}；极分解相对 L2 {fmt(transport["checks"]["inverse_polar_rotation_relative_L2"])}；步长减半的增量协方差误差约减半。','physics_isolated.py transport',['physics/outputs/gaussian_transport/metrics.json','physics/outputs/gaussian_transport/reference_arrays.npz'])
    add('V17','失败','发布代码的非单位预旋转 SH 坐标不变性','本轮重执行原 convert_SH 函数的刚性物体/相机同步旋转试验：identity 情况通过，但非单位预旋转情况下原路径不能保持颜色不变。局部外部共轭变换适配器通过不变量测试；Ficus 的 Q=I 不触发此问题。测试器返回 0 表示成功检出了负例，不代表上游原路径通过。实测：'+json.dumps(sh['records'],ensure_ascii=False)+'。','physics_isolated.py sh',['physics/outputs/sh_frame_audit/metrics.json','physics/outputs/sh_frame_audit/color_reference.npz'])
    add('V18','通过','已存在 SH 外部适配器的局部测试','本轮重测的 QᵀR⁻¹Q 转换在三种预旋转下均保持参考颜色。只验证函数及已有纠正视频的文件内容；本轮没有重跑 bread/plane/vasedeck 三个完整纠正场景。','physics_isolated.py sh；media_and_syntax.py',['physics/outputs/sh_frame_audit/metrics.json','checks/video-decode.json'])
    add('V19','失败','snow 材料的实际本构支持','本轮实际运行原应力核：snow 映射为 material=4，但发布应力核缺少该分支，加载/卸载过程应力始终为零。测试器对此负例有断言，因此脚本正常退出不能称 snow 材料已成功复现。','materials_isolated.py（原 validate_materials，仅输出/缓存重定向）',['materials/outputs/material_audit/metrics.json','materials/outputs/material_audit/snow.npz'])
    add('V20','通过','其他材料的规定变形核心检查',f'jelly 弹性解析应力相对误差 {fmt(material["elastic_analytic_relative_error"])}、客观性误差 {fmt(material["objectivity_relative_error"])}；刚性旋转、沙均匀张拉和 metal/foam/plasticine 的加载卸载均完成原检查。此处是单粒子规定变形本构试验，不代表各材料论文空间场景验证。','materials_isolated.py',['materials/outputs/material_audit/metrics.json','materials/outputs/material_audit/stress_paths.png'])
    add('V21','通过','各向异性正则函数与旧 PLY 实测',f'本轮独立随机案例验证原函数的损失、解析梯度、gradcheck 与统一缩放不变性，梯度最大绝对差 {fmt(aniso["analytic_gradient_max_error"])}。原始 PLY 重测平均轴比：无正则 {fmt(aniso["saved_PLY_readback"][0]["mean_ratio"])}，有正则 {fmt(aniso["saved_PLY_readback"][1]["mean_ratio"])}。不把这当作本轮重训结果。','check_anisotropy.py',['checks/anisotropy.json'])
    add('V22','通过','已有模拟与音频产物内容检查','独立读取 11 个已有最终物理状态，检查有限性、位移、质量记录；逐帧解码 11 个视频，抽取首/中/末帧并实际查看全部拼图。PAT/扩展/移动听者/NeuralSound WAV 与对应原始数组和共同增益精确一致。NeuralSound 已有音频对 BEM 原始声压相对 L2 为 107.068%，文件有效不代表预测精确。没有进行人类听感实验。','independent_cpu.py；media_and_syntax.py；audio_readback.py',['checks/saved-physics.json','checks/video-decode.json','checks/audio-readback.json','可视化核查记录.md'])
    add('V23','通过','全部本地 NeuralSound BEM 标签重新生成','24 个几何、144 模态标签全部使用发布的 Bempp 算子重新计算，保持现有 NumPy 兼容/Numba CPU/双精度/1e-8 容差适配，所有 GMRES 实测残差达标。新旧近场/远场数组逐值相同。起点仍是已有体素振动模态，不代表已重新生成 ABC 数据。','labels_job.py → labels_isolated.py',['commands/fresh-bem-labels.json','checks/fresh-bem-labels.json','neural_labels/inputs/procedural_bempp/dataset.json'])
    add('V24','通过','已有神经权重及完整训练状态可读性','8 个 best/last 检查点实际加载，模型和优化器张量有限；last 的 epoch、完整 history、scheduler、RNG 状态核对一致。辐射 best 的选取 epoch 与验证集最低 loss 一致。权重可读性不证明本轮重复了训练历史。','checkpoint_readback.py',['checks/checkpoints.json'])
    add('V25','通过','两套辐射权重的全测试集新推理','直接从原始 NPZ 独立构建 23 通道特征，运行公开 AcousticNet；两个 profile 各 24 张测试图，新推理与旧预测导出相对差 '+', '.join(fmt(x['new_vs_old_prediction_relative_L2']) for x in inference)+'。全体新预测/参考图均保存并视觉检查。','neural_inference.py',['neural/radiation_training/predictions.npz','neural/radiation_paper_schedule/predictions.npz','可视化核查记录.md'])
    add('V26','失败','当前本地辐射网络作为高精度 FFAT 近似','新推理的平均原始 FFAT 相对 L2：发布代码训练 profile '+f'{inference[0]["mean_relative_L2"]:.3%}'+', paper-schedule 本地对照 '+f'{inference[1]["mean_relative_L2"]:.3%}'+ '；均劣于逐样本相对 L2 恒为 100% 的全零输出基准。此均值会受低辐射模式放大，故同时记录中位数、逐样本误差、负值比例与归一化指标。两个 profile 的归一化 map MSE 分别 '+', '.join(fmt(x['normalized_map_MSE']) for x in inference)+'，自然对数幅值 MSE 分别 '+', '.join(fmt(x['natural_log_amplitude_MSE']) for x in inference)+'。这不能证明论文精度；也不能将百分比直接对比论文表 5 的 0.06/0.07。','neural_inference.py',['neural/radiation_training/metrics.json','neural/radiation_paper_schedule/metrics.json'])
    add('V27','通过' if all(x['passed'] for x in vibration) else '失败','两套振动权重的实际混合求解',f'4 个测试几何 × 2 组权重，重新运行网络初始化加 LOBPCG，并独立组装物理 K/M 与 SciPy 稠密特征值参考。逐弹性模态最大残差 {fmt(max(x["max_elastic_residual"] for x in vibration))}，最大相对特征值误差 {fmt(max(x["max_elastic_eigenvalue_error"] for x in vibration))}。这验证最终求解精度，不证明网络本身贡献或论文加速比。','vibration_rerun.py',['neural/vibration-fresh-solves.json','neural/vibration_training/network-validation.json','neural/vibration_paper_schedule/network-validation.json'])
    add('V28','未验证','未重复的训练与全部扩展场景','本轮没有从零重训两套 NeuralSound 振动/辐射网络的 100/200 epoch 全部配置，没有重训各向异性 30,000 步模型，没有重跑所有 11 条已有动态场景及所有移动听者/扩展音频链路。对这些内容仅报告本轮实际完成的权重/数组/图像/音频检查，不沿用旧日志的 completed 结论。','未执行完整重复训练/全部场景',['验收标准.md'])
    add('V29','未验证','三篇论文原始数据、架构与完整指标/性能复现','PhysGaussian Table 1 是 Wolf/Stool/Plant 弯曲扭转的专门合成变形基准（未变形训练 100 视角，各变形状态 100 真值视角）；静态 Ficus 指标不替代它。NeuralSound 使用约 100K ABC、随机材质/模态和 4:1:1 划分；本地仅 24 个程序化几何。公开 README 明说 AcousticNet 比论文架构紧凑，论文 Mel 频率分支与公开特征编码也不同。paper-schedule 只对齐部分优化参数。未完成论文 100 个测试物体×20 模态基准、3080Ti/3090 性能比较、听感实验等。PAT 差距另见 V09。','论文原文、README、代码与本地输入核对；对应论文完整基准未执行',['papers/01_PhysGaussian.txt','papers/03_NeuralSound.txt','papers/03_NeuralSound_page10.png','papers/sources.json'])
    add('V30','未验证','全新机器环境恢复与远端资源真实性','本轮使用已有 Conda 环境，重编译了所述 C++/CUDA 模块，未从空环境重装所有依赖。没有重新从远端获取并认证全部数据、权重和资源；本地哈希匹配只能证明当前文件与本地来源记录一致。','未执行全新环境安装及全部资源远端复核',['checks/data.json','checks/environment-export-text.json'])
    add('V31','未验证','统一的同一 3DGS 物体受力—振动—声辐射系统','当前验证的 Ficus 3DGS、程序化体素梁/盒子声学和 NeuralSound 数据是不同输入。没有发现或完成同一 3DGS 对象连续驱动受力、振动、声辐射并同步验收的统一演示。原计划把它列为研究背景；三个目录和局部模块成功不自动实现这一研究系统。','本轮各实际命令与输入路径核对；统一系统未执行',['验收标准.md','command-index.json'])
    add('V32','通过','本轮未修改既有代码、配置、数据和结果',f'开始前采集 {protected["files"]} 个既有文件 SHA256，结束后重新扫描：changed={len(protected["changed"])}, missing={len(protected["missing"])}, added={len(protected["added"])}。新测试脚本、缓存、构建、模型、图像、音频、报告均位于 verification_20261101。保护快照排除 Conda 安装、Git 内部、__pycache__ 和运行缓存；不夸大为整个系统零文件变化。','snapshot_originals.py before / after',['original-files-before.json','original-files-after.json'])
    for item in items:
        if item['id'] in ('V19','V20'):
            item['evidence']=[p.replace('materials/','materials_linux/') for p in item['evidence']]
            item['commands']='materials_linux_job.py → materials_linux.py（原数值函数不变；Linux 不使用 Windows 专用包含路径钩子）'
            item['detail']+=' Windows 隔离缓存路径含中文，首次尝试在编译阶段失败；Linux 重试的原数值检查实际完成。'
            item['evidence']+=['materials_linux/adapter.json','logs/materials-fresh-windows.log']
        if item['id']=='V15':item['detail']=item['detail'].replace('最大位移','MPM 坐标中最大位移')
        if item['id']=='V26':
            item['detail']+=f' 两套权重的原始相对 L2 中位数分别为 {inference[0]["median_relative_L2"]:.3%} 和 {inference[1]["median_relative_L2"]:.3%}；视觉上大部分预测仍未恢复参考的平滑方向性波瓣。'
        if item['id']=='V12' and not native['passed']:
            if (AUDIT/'checks/native-entry-stop.json').exists():
                stopped=get('checks/native-entry-stop.json');item['status']='未验证'
                item['detail']=f'原 metrics.py 已实际启动，最终完成 {stopped["completed_views"]}/200 张；进程运行 {stopped["process_elapsed_s"]:.1f} 秒，最后进度显示 {stopped["last_progress"]}。源码核对确认 lpips() 对每张图重新构造网络。本轮因预计额外耗时超过一小时，仅向核实过命令行的该验证子进程发送 SIGTERM（退出 -15），保留日志及停止记录。完整原入口未完成，不能推断通过，也没有把它误写成显存不足。V11 的全部 200 张独立流式评估已完成，二者分开判断。'
                item['evidence']+=['checks/native-entry-stop.json','commands/captured-stop_native_entry.json']
            if (AUDIT/'checks/native-metrics-exceptions.json').exists():
                exceptions=get('checks/native-metrics-exceptions.json')
                if any('out of memory' in e['message'].lower() for e in exceptions):
                    item['status']='未验证';item['detail']+=' 实际异常追踪确认 CUDA out of memory，因此原全量入口在本机 4GB 显存下未完成，按硬件限制标为未验证；不是推断失败原因。'
                item['evidence']+=['checks/native-metrics-exceptions.json','logs/captured-diagnose_native_metrics.log']
            if native['command'].get('exit_code') is None:
                item['status']='未验证';item['detail']+=' 此次原入口因记录中的超时或启动异常未完成，不能推断通过。'
    save('逐项验收.json',items)
    counts={s:sum(i['status']==s for i in items) for s in ('通过','失败','未验证')}
    lines=['# 三篇论文复现工作独立验证报告','',f'验证日期：2026-11-01；报告生成：{stamp()}。工作目录：`F:/System/Desktop/3DGS/复现`。','',
'## 1. 原始目标与验收口径','',
'原始聊天要求：阅读复现计划后执行，优先 Conda；按 PhysGaussian、PAT、NeuralSound 三篇分成三个文件夹，完成可行复现并把记录写入文档。后续“继续所有内容”的授权扩大了执行范围，但不改变科学验收要求。本次请求只允许验证，不允许修改既有代码或结果。','',
'原计划最低目标是 A1 模态声音原理实验、对照与官方可行性核查；进一步才是作者模块、本地完整流程以及按论文数据/设置/指标进行结果复现。本文先列明这些层级，分别判断；不将之前的“已完成”文案、文件存在、日志状态字段当作通过证据。预定标准见 [验收标准](验收标准.md)。','',
'通过＝本轮实际执行且达到所述局部检查；失败＝实际反例/不满足所述条件；未验证＝本轮未执行或缺乏可比参考。检查程序正常退出不等于其发现的负例通过。原脚本复用处明确标出，辅以独立数学/数据/像素检查。','',
'## 2. 结论','',
'**目前不能称为三篇论文完整复现成功，也不能称所有工作已经验收完成。** 原计划 A1 最低实验已得到独立数值支持；本地 3DGS 训练—渲染—评估—物理模拟、若干作者数值模块及本地声学链路已有真实运行证据。但当前仍有可复现的负结果，以及未执行的完整论文基准/全训练重复。','',
f'本报告按 32 个明确范围逐项列为：通过 {counts["通过"]} 项，失败 {counts["失败"]} 项，未验证 {counts["未验证"]} 项。该数量不是论文完成百分比。','',
'主要差距：Windows 环境导出路径损坏；原 SH 非单位坐标变换不变量失败；snow 无有效应力分支；本地辐射网络预测误差大；幅值声学合成对等价模态基敏感。论文数据、公开/论文网络差异、完整原场景与加速/听感基准仍未对齐。此次仅记录，不修复。','',
'## 3. 逐项验证','']
    for item in items:
        lines.extend([f'### {item["id"]}　{item["status"]}：{item["title"]}','',item['detail'],'',f'实际命令/入口：`{item["commands"]}`。完整 argv、工作目录、退出码、耗时及日志见 [命令索引](命令与日志索引.md)。','', '证据：'+'；'.join(f'[{p}]({p})' for p in item['evidence'])+'。',''])
    lines.extend(['## 4. 执行中失败尝试与验证限制','',
'- Windows 通用探针导入 SciPy 失败：该旧 Warp 环境未安装 SciPy，而其实际入口不依赖它；按实际依赖的修正探针通过。pat-tools 的 Python 探针失败：该前缀只有 C++ 库，后续真实链接验证通过。原错误均保留。',
'- 首次 WSL PAT 启动失败，尚未执行构建；重试后构建与数值程序退出 0。一次媒体检查的外层 PowerShell 因 WSL stderr 包装返回非零，后来用 subprocess 捕获真实子进程返回 0，并保留两次日志。',
'- fresh-fem-pat-chain 首次因 WSL Git 的 CRLF 判定被原脚本中止。独立逐文件核对无实质源码差异后，仅对重试进程设置 core.autocrlf=true，未修改 Git 配置；新目录重试通过。失败日志及部分新产物保留在 verification_20261101。',
'- LPIPS 使用固定上游实现和本地缓存权重；PSNR 使用 8 位输出 PNG，因此与训练期间浮点图像指标可能略有差异。物理模拟、构建和推理串行使用 GPU；本轮耗时不是论文可比较的性能实验。',
'- 视觉检查记录见 [可视化核查记录](可视化核查记录.md)，包括实际看过的图。未做真人听感测试，也没有对每张图逐像素作主观评级。',
'- 不把局部校验函数的自报 passed 当作唯一证据：本轮另外做了闭式频率/全波形、真实 GT 合成、独立特征编码、逐样本 PCM、源码/文件哈希、模态子空间不变量等交叉检查。',
'', '## 5. 验收后应优先补的工作（本轮未实施）','',
'1. 修复并从空 Conda 环境验证导出/安装流程。',
'2. 对 SH 坐标变换、snow 支持范围和声学模态基敏感性作明确修复或限制声明，再重跑对应验收。',
'3. 扩展 NeuralSound 的数据分布，重新训练并设立独立精度基准；不能只因训练完成便宣称声学近似成功。',
'4. 获取并复现各论文匹配的场景、设置、评价定义及性能协议；同一 3DGS 物体的统一声音系统另设端到端验收。',
'', '本次交付的可重复证据集中于此目录；既有总报告和各项目结果保持原样。',''])
    lines.extend(['## 6. Windows 材料核隔离路径失败与 Linux 重试','',
        'Windows Warp 0.10.1 实际返回 Failed to open output file，目标是本轮带中文的隔离缓存路径；材料应力核尚未执行。因此不把这次 Windows 尝试标为材料数值通过。Linux 重试使用同一发布核与相同测试函数，仅改输出/缓存路径并省略 Windows 专用 include-path 钩子，实际完成所有规定变形检查。没有修改原 Windows 代码或环境。见 [失败日志](logs/materials-fresh-windows.log)、[Linux 命令](commands/materials-fresh-linux.json) 与 [适配说明](materials_linux/adapter.json)。',''])
    (AUDIT/'独立验证报告.md').write_text('\n'.join(lines),encoding='utf-8');print(json.dumps(counts,ensure_ascii=False))
if __name__=='__main__':main()
