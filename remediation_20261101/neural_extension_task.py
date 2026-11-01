import sys,importlib,json
from common import ROOT,AUDIT
sys.path.insert(0,str(ROOT/'03_NeuralSound/code'))
isolated=AUDIT/'neural_extensions'
for part in ('inputs','outputs','docs'):(isolated/part).mkdir(parents=True,exist_ok=True)
links={'inputs/procedural_bempp':ROOT/'03_NeuralSound/inputs/procedural_bempp','outputs/vibration_training':AUDIT/'neural/outputs/vibration_training','outputs/radiation_training':AUDIT/'neural/outputs/radiation_released_profile'}
for dst,source in links.items():
 if not (isolated/dst).exists():(isolated/dst).symlink_to(source,target_is_directory=True)
task=sys.argv[1];sys.argv=[sys.argv[0],*sys.argv[2:]]
if task=='example':
 import run_official_example as m
 m.ROOT=isolated;m.main()
elif task=='hybrid':
 import run_example_hybrid as m
 m.local.ROOT=isolated;m.main()
 extended='--extended' in sys.argv;tag='example_hybrid_ood_extended' if extended else 'example_hybrid_ood'
 result=json.loads((isolated/'outputs'/tag/'metrics.json').read_text())
 lines=['# 本轮作者网格混合模态求解','',f"实际体素数 {result['occupied_voxels']}、自由度 {result['degrees_of_freedom']}，预算 {result['iteration_limit']} 次迭代，输出 {result['elastic_modes']} 个弹性模态。",'',
 '本轮在执行协议中预先固定 2000 与 10000 两种预算，分别输出，不根据测试结果调整网络。几何不属于本地长方体训练族。','']
 for r in result['records']:lines.append(f"- {r['initialization']}：迭代 {r['iterations']}，特征值最大相对误差 {r['max_eigenvalue_relative_error']:.6g}，最大残差 {r['max_relative_residual']:.6g}，收敛标记 {r['converged']}。")
 lines+=['',f'[本轮完整记录](../outputs/{tag}/metrics.json)。高精度若获得，来自网络初始化与严格数值精修的组合；一次壁钟记录不作为论文性能。']
 (isolated/'docs'/('EXAMPLE_HYBRID_OOD_EXTENDED.md' if extended else 'EXAMPLE_HYBRID_OOD.md')).write_text('\n'.join(lines)+'\n',encoding='utf8')
elif task=='acoustics':
 import run_example_acoustics as m
 m.ROOT=isolated;m.prepare();m.predict('cuda:0')
 result=json.loads((isolated/'outputs/example_acoustic_ood/metrics.json').read_text());reference=result['reference']
 lines=['# 本轮作者网格的声辐射泛化检查','',
 f"实际体素数 {reference['occupied_voxels']}；固定前两个 Ceramic 模态的频率为 "+'、'.join(f'{f:.3f} Hz' for f in reference['frequencies_Hz'])+'。', '',
 '使用本轮独立 FEM 参考与原 Bempp 双精度算子。若 GMRES 未达标，在同一组装方程上使用直接 LU；不放宽残差要求。每次实际求解记录如下：','']
 for r in reference['bem_solves']:lines.append('- '+json.dumps(r,ensure_ascii=False))
 lines+=['',f"冻结本轮 released_profile 模型，CUDA 推理两张图的平均原始相对 L2 为 {result['test']['mean_transfer_relative_L2']:.4%}。没有为此物体选权重或调参。",'',
 '本轮 GPU 重任务串行执行；没有与狼场景并行，也没有人为暂停这次 BEM 计时。此处未重跑 CPU 推理，旧文档中的 CPU 全局池化失败属于历史记录；不将其写成本轮新测试。', '',
 '[实际指标及参考残差](example-acoustic-ood-metrics.json) · [参考/预测图](../outputs/example_acoustic_ood/maps.png)。这是两模态的局部泛化检查，不是完整 ABC 基准，也不是该网格的神经振动到声辐射端到端系统。']
 (isolated/'docs/EXAMPLE_ACOUSTIC_OOD.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
elif task=='audio':
 import run_neural_audio as m
 m.ROOT=isolated;m.main()
else:raise ValueError(task)
