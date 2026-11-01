"""Finalize scoped acceptance only after actual jobs and artifact audits finish."""
import json
from common import ROOT,AUDIT,save,stamp
def read(p):return json.loads((AUDIT/p).read_text(encoding='utf-8-sig'))
for name in ['gpu-queue','gpu-followup','gpu-final','post-gpu','unified-neural','clean-pat','example-retry']:
 assert (AUDIT/(name+'-complete.json')).exists(),name+' still pending'
art=read('checks/final-artifacts.json');syntax=read('checks/source-and-syntax.json')
checks=[]
def entry(id,status,summary,evidence,limits):
 original=next(d for d in read('scope.json') if d['id']==id)
 checks.append(dict(id=id,original_status=original['previous_status'],title=original['title'],status=status,summary=summary,evidence=evidence,limits=limits))
entry('V03','通过' if read('checks/V03.json')['passed'] else '失败',
 '三份 Windows 导出已修复；两种不同规格从空 Conda 前缀恢复，并实跑 CPU SH 与声学流程。',
 ['checks/V03.json','checks/V03-clean-windows-phys.json','checks/V30-clean-cpu.json'],
 'Windows PhysGaussian 这里只验证 CPU 路径；CUDA 实跑记录在 V30。')
a=read('checks/V08.json');b=read('checks/V08-extensions.json')
entry('V08','通过' if a['passed'] and b['passed'] else '失败',
 f"本地相位扩展通过符号、重根旋转和独立 FEM 基不变性。6 模态 PAT/BEM 音频误差 {a['PAT_vs_BEM_audio_relative_L2']:.4%}；移动听者 {b['moving_PAT_BEM_audio_relative_L2']:.4%}。",
 ['checks/V08.json','checks/V08-extensions.json','figures/basis_invariance.png'],
 '通过的是新相位扩展；旧幅值路径仍保留其失败。窄带 Hilbert 合成不包含完整传播延迟、Doppler 或瞬态接触声学。')
c=read('checks/V09-convergence.json')
entry('V09','未验证',
 '均匀 Neumann 球体 80/320/1280/5120 面片误差依次为 '+ '、'.join(f"{r['relative_complex_error']:.4%}" for r in c['rows'])+'，不完全单调；精确单极子制造解另有单调收敛证据。',
 ['checks/V09-convergence.json','checks/V09-manufactured.json','figures/bem_refinement.png'],
 '原收敛判据没有通过；制造解边界条件不同。NeoAcoustics、原论文全部场景、薄壳/高频、多层算法、7000 倍性能与听感实验仍未完成。')
v=read('checks/V12.json')
entry('V12','通过' if v['passed'] else '失败',
 '未修改作者 metrics.py 实际评估 200/200 图：PSNR 34.8505973816，SSIM 0.9871883988，LPIPS 0.0117154643；与独立流式评估一致。',
 ['checks/V12.json','outputs/native_metrics/results.json','outputs/native_metrics/per_view.json','commands/V12-original-metrics-all200.json'],
 '这验证原始评估入口与当前 Ficus 重建，不是 PhysGaussian 变形真值基准。')
sh=read('physics/outputs/sh_frame_audit/metrics.json')
shpaths=[f'physics/outputs/{n}_corrected_rerun/metrics.json' for n in ['bread','plane','vasedeck']]
sh_ok=sh['adapter_checks_passed'] and all(read(p)['all_checks_passed'] and read(p)['sh_frame_correction'] for p in shpaths)
entry('V17','通过' if sh_ok else '失败',
 '本地入口默认世界坐标 SH 修正，保留 legacy 对照；不变性和 bread/plane/vasedeck 三个完整场景已重跑，保存同状态原始/修正渲染及原始浮点数组。',
 ['physics/outputs/sh_frame_audit/metrics.json',*shpaths,'checks/final-artifacts.json'],
 '修复在外部适配器，作者上游源码仍有原坐标系问题；无变形真值时不能用画面变化声称论文指标提升。')
sn=read('checks/V19-snow-extension.json')
snow_ok=sn.get('passed',sn.get('all_checks_passed',False)) and read('physics/outputs/snow_ficus_local/metrics.json')['all_checks_passed']
entry('V19','通过' if snow_ok else '失败',
 '新增 snow 本构适配器，通过独立 NumPy 应力参考、125 粒子 4000 步接触，以及 Ficus 几何 171553 粒子/10000 步/25 帧 CUDA 场景。',
 ['checks/V19-snow-extension.json','checks/V19-snow_ficus_local.json','figures/snow_validation.png','physics/outputs/snow_ficus_local/output.mp4'],
 '这是固定参数的本地弹塑性雪扩展，不是作者已发布的 snow 或实测材料标定；旧 upstream 分支仍保留。')
rad=read('checks/V26-independent.json')
rad_ok=len(rad)==3 and all(r.get('inference_completed') and r.get('all_maps_below_10percent') for r in rad)
entry('V26','通过' if rad_ok else '失败',
 '三套完整训练后独立重编码全部 24 张测试图：'+ '；'.join(r['tag']+f" 平均/中位/最坏相对 L2={r['mean_relative_L2']:.2%}/{r['median_relative_L2']:.2%}/{r['maximum_relative_L2']:.2%}，全局加权 L2={r['global_relative_L2']:.2%}" for r in rad),
 ['checks/V26-independent.json',*[f"neural/evaluations/{r['tag']}/metrics.json" for r in rad],*[f"neural/evaluations/{r['tag']}/shape_and_amplitude.png" for r in rad]],
 '10% 逐图线仅为严格本地诊断，不是论文 Table 5。全部模型只按验证损失选 best；不按测试表现挑选或隐藏失败。完成训练不等于高精度。')
required=[r for r in read('gpu-queue-state.json') if r['name'].startswith('V28-') or r['name']=='V26-radiation-longer']+read('gpu-followup-state.json')+[r for r in read('gpu-final-state.json') if r['name'].startswith('V28-')]
scene_rows=[r for r in art['video_and_scene_checks'] if 'scene' in r and not r['scene'].startswith('snow')]
retry=read('checks/V28-example-retry.json')
retry_numerics=read('checks/V28-example-retry-numerics.json') if (AUDIT/'checks/V28-example-retry-numerics.json').exists() else {}
recovered=retry['passed'] and retry_numerics.get('passed',False)
unresolved=[r for r in required if r['exit_code']!=0 and not (r['name']=='V28-neural-example' and recovered)]
repeat_ok=not unresolved and len(scene_rows)==11 and art['passed'] and read('checks/V28-pat-extensions.json')['passed']
entry('V28','通过' if repeat_ok else '失败',
 f"重复网络训练、30000 步各向异性训练/200 视图渲染与评估、11 个物理场景、12 模态/移动听者、作者网格/混合优化与神经音频。原队列要求内命令 {len(required)} 条，首次失败 {sum(r['exit_code']!=0 for r in required)} 条，恢复后未解决 {len(unresolved)} 条；完成核查的物理场景 {len(scene_rows)} 个。作者 example 首次退出 -11，隔离 PyCUDA 体素化与 Torch 求解后完整重跑及数值对照通过={recovered}；首次失败日志仍保留。",
 ['gpu-queue-state.json','gpu-followup-state.json','gpu-final-state.json','checks/V28-example-retry.json','checks/V28-example-retry-numerics.json','checks/V28-pat-extensions.json','checks/V28-anisotropy-comparison.json','checks/final-artifacts.json'],
 '通过仅指这些本地扩展被重复执行且产物有效；其精度仍分别受 V08/V26 等限制，不将执行成功当作论文复现。')
entry('V29','未验证',
 '复核三篇论文数据、模型与评测要求；本机仍未完成全部原始数据/架构/性能与听感协议。',
 ['未能完成的论文级要求.md','checks/V29-public-resource-inventory.json'],
 '24 个程序化几何不等于 100K ABC；公开紧凑网络不等于论文网络；静态 Ficus 不等于变形真值；RTX 2050 不替代 3080 Ti/3090，未组织受试者实验。')
fresh=['checks/V30-clean-gpu-execution.json','checks/V30-clean-neural-execution.json','checks/V30-clean-pat-execution.json']
entry('V30','未验证',
 '两种 Windows 与三种 Linux Conda 前缀已从空目录恢复；CUDA/C++ 重新构建并实跑。新 Linux 环境执行状态：'+str({p:read(p)['passed'] for p in fresh})+'。403 个 Ficus 文件与当前作者数据包逐字节一致，作者仓库/六份模型/使用的源码依赖均重新远端核对。',
 ['checks/V03.json',*fresh,'checks/V30-canonical-ficus-updated-folder.json','checks/V30-dependency-sources.json','checks/V30-remote.json','checks/V30-remote-models.json'],
 '仍在同一台物理机器、同一驱动与 WSL 上；另一台新机器尚未验证。HTTPS 内容匹配不是作者数字签名认证。旧作者 Drive 链接 404 的失败记录保留。')
entry('V31','未验证',
 '新增同 FEM 梁的高斯/PAT/BEM 同步原型，以及同 held-out box_21 的混合模态/AcousticNet/高斯原型，分别导出真实速度与标注放大/慢动作视频。',
 ['checks/V31-local-prototype.json','checks/V31-neural-box-prototype.json','checks/final-artifacts.json','unified_beam/metrics.json','unified_neural_box/metrics.json'],
 '过程生成高斯不等于照片训练的 3DGS；没有完成照片高斯—体积绑定、MPM 接触—高频振动与神经声辐射完整耦合。神经原型仍保留幅值 FFAT 与预测误差，完整目标未通过。')
counts={s:sum(c['status']==s for c in checks) for s in ['通过','失败','未验证']}
scope=read('scope.json')
for row in scope:row['new_status']=next(c['status'] for c in checks if c['id']==row['id'])
save('scope.json',scope)
save('最终验收状态.json',dict(generated=stamp(),counts=counts,items=checks,artifact_audit_passed=art['passed'],source_audit_passed=syntax['passed'],paper_reproduction_success=False))
lines=['# 5 项失败 + 6 项未验证：补做验收报告','',
 '结论：目前仍不能称为三篇论文完整复现成功。本轮修复并验证了若干本地问题、补齐多项实际执行证据；没有把受硬件、数据、原架构与实验协议限制的目标改写成通过。', '',
 f"最终按原 11 项统计：通过 {counts['通过']} 项，失败 {counts['失败']} 项，未验证 {counts['未验证']} 项。通过项的范围和保留限制如下；特别是 V08/V17/V19 属本地修复，不表示未改作者实现本身已通过。",'',
 '历史 `../verification_20261101` 保留。新增命令、失败尝试、日志、模型、媒体和检查均记录在本目录。每条实际命令见[命令与输出索引](命令与输出索引.md)，机器可读状态见[最终验收状态](最终验收状态.json)。','']
for c in checks:
 lines += [f"## {c['id']} {c['title']}：{c['status']}",'',c['summary'],'', '**边界与差距：** '+c['limits'],'','证据：','']
 lines += [f'- [{p}]({p})' for p in c['evidence']];lines += ['']
lines+=['## 补充数值：不把命令退出 0 当作精度达标','']
for r in rad:
 lines += [f"- {r['tag']}：归一化方向图 MSE={r['normalized_map_MSE']:.6g}，自然对数幅值 MSE={r['natural_log_amplitude_MSE']:.6g}，原始负预测比例={r['negative_fraction']:.4%}。最佳检查点 epoch={r['selected_epoch']}，只按验证损失选择。"]
lines+=['']
example=read('neural_example_retry/outputs/official_example/metrics.json') if recovered else read('neural_extensions/outputs/official_example/metrics.json')
lines += [f"作者 example 首次在输出结果后发生原生段错误（退出 -11），疑似 PyCUDA/Torch CUDA 上下文生命周期冲突，不能仅凭输出文件认定成功。后续分进程正常退出的完整重跑通过={recovered}。下述 example 数值取自{'成功重跑' if recovered else '首次失败尝试，尚不能认定执行通过'}；后续混合优化/声学保留首次产物，已独立核对两次 FEM 质量和刚度矩阵逐元素完全相同、参考特征值一致且参考残差合格。根因仍只作推测，没有将它当作已证明的 CUDA 缺陷。",'']
lines += [f"作者 example.obj 的原始 LOBPCG 最大相对残差为 {max(example['official_relative_residuals']):.6g}，特征值最大相对误差 {max(example['eigenvalue_relative_errors']):.6g}；独立双精度参考最大残差 {max(example['reference_relative_residuals']):.6g}。原始求解器的误差保留，不能用参考解精度替代它。",'']
for tag in ['example_hybrid_ood','example_hybrid_ood_extended']:
 h=read(f'neural_extensions/outputs/{tag}/metrics.json')
 lines += [f"混合模态预算 {h['iteration_limit']}：",'']
 for r in h['records']:
  lines += [f"- {r['initialization']}：最大特征值相对误差 {r['max_eigenvalue_relative_error']:.6g}，最大残差 {r['max_relative_residual']:.6g}，收敛={r['converged']}。"]
 lines += ['']
ood=read('neural_extensions/outputs/example_acoustic_ood/metrics.json');sound=read('neural_extensions/outputs/neural_audio/metrics.json')
lines += [f"原作者网格两张 FFAT 的平均原始相对 L2={ood['test']['mean_transfer_relative_L2']:.3%}。这项几何外推实验使用本轮 released_profile 检查点，不是额外训练或对该网格调参。",'',
 '同 box_21 的三处听者神经/BEM 音频相对 L2 依次为 '+ '、'.join(f'{x:.3%}' for x in sound['per_listener_audio_relative_L2'])+'。此链路使用刚度缩放后的 Ceramic 参数作受控演示，不是实测陶瓷；仍采用幅值 FFAT，不能借用 PAT 相位扩展的基不变性结论。','',
 '[作者网格模态成功重跑](neural_example_retry/outputs/official_example/metrics.json) · [首次失败产物](neural_extensions/outputs/official_example/metrics.json) · [两图声辐射](neural_extensions/outputs/example_acoustic_ood/metrics.json) · [三听者声音](neural_extensions/outputs/neural_audio/metrics.json)。','']
aniso=read('checks/V28-anisotropy-comparison.json')
lines += ['本轮各向异性 30000 步重建的 200 图指标：'+ '；'.join(f'{k}={v:.8g}' for k,v in aniso['evaluation'].items())+'。','']
baseline=read('outputs/native_metrics/results.json')['ours_30000']
lines += ['相同正式评估口径下，本轮各向异性模型减去基线的指标变化：'+ '；'.join(f"{k}={aniso['evaluation'][k]-baseline[k]:+.8g}" for k in ['PSNR','SSIM','LPIPS'])+'。PSNR/SSIM 越高、LPIPS 越低通常越好；本轮结果并未提升这三项静态图像指标。约束轴长比与提升图片质量是不同目标，不能把新训练一概描述为优于基线。','']
for r in aniso['models']:lines += [f"- {r['model']}：{r['gaussians']} 个高斯，平均轴长比 {r['mean_axis_ratio']:.6g}，中位轴长比 {r['median_axis_ratio']:.6g}，轴长比>5 占 {r['fraction_above_5']:.3%}。"]
lines += ['','[固定视角图像对照](figures/ficus_reconstruction_comparison.png)使用预先固定的第 0/50/100/150 个测试视角，全部 200 张参考图已逐字节核对。质量评价以全部视角指标为准，不只看四张图。','']
psnr=read('checks/V28-psnr-definition.json')
lines += [f"训练日志与正式评估的 PSNR 定义不同：作者 train.py 向 psnr() 传入 CHW，实际分别计算三个通道的 dB 再平均；metrics.py 传入 NCHW，每张图先合并 RGB 的均方误差再计算 dB，最后平均视角。本轮对相同 200 张 PNG 独立复算：通道 dB 平均={psnr['PNG_mean_channel_PSNR']:.8f}，每图 RGB 合并={psnr['PNG_global_RGB_PSNR']:.8f}，定义差 {psnr['channel_aggregation_difference_dB']:.8f} dB；训练浮点图日志={psnr['training_float_tensor_channel_PSNR']:.8f}，与 PNG 通道平均仍有 {psnr['training_minus_PNG_channelwise_dB']:.8f} dB 差。没有混用这两个统计量宣称质量提升。[实际计算与源码哈希](checks/V28-psnr-definition.json)。",'']
lines += ['## 产物与源码核查','',f"实际解码视频 {len(art['video_and_scene_checks'])} 条、WAV {len(art['wav_checks'])} 条；产物审计通过={art['passed']}。PNG 尺寸、帧数/fps、音轨起点/时长、数组/PLY 有限性、SH 同状态原始数组与图片一致性均留有检查记录。",'',
 '首次完整产物审计在花瓶 SH 数组核对时失败。诊断确认 2995×3994×3 的数组在本机 Linux NumPy float32 范数累积中有误差：第 25 帧得到 0.0624776483，而 GPU 记录 0.0625215918；独立 float64 为 0.0625215917，PNG 与数组量化后逐字节一致。验证器改用 float64 累积后，重新核验全部三个场景的 12 组数组/24 张配对 PNG，原 1e-6 数值阈值和 1 字节图像阈值均保持不变；已完成的 19 视频、24 WAV 和两份 PLY 用哈希复核后沿用原解码检查。首次失败[完整审计](checks/final-artifacts-first-attempt.json)、[Linux 诊断](checks/SH-artifact-diagnostic-linux.json)和[针对性复核](checks/SH-artifact-precision-recheck.json)均保留，没有改动模拟或渲染结果。','',
 '额外发现：狼场景的原作者代码使用 int(frame_dt/substep_dt)，浮点舍入使每帧少一个子步，50 帧累计实际模拟 1.999 秒，而视频名义时长 2 秒。本轮保留原始仿真语义，分别记录真实模拟时间与视频时间，不声称该差异为零。此场景无音轨；两个新增有声原型另用共享时间轴并核对封装后的音画时长。','',
 '源码与语法边界见[检查结果](checks/source-and-syntax.json)，已修改包装器的前后差异见[补丁](local_changes.patch)。作者三个主仓库源码保持不变；新增本地扩展单独标注。', '',
 '查看具体视频和图像见[本轮结果查看指南](本轮结果查看指南.md)；实际打开图片后的观察、视野裁切和预测失真见[视觉核查记录](可视化人工核查.md)。未开展人类听感研究；WAV 数值与解码检查不能代替主观听音实验。']
(AUDIT/'补做验收报告.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print(counts,flush=True)
