"""Generate extension reports exclusively from completed, independently audited runs."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageOps,ImageDraw

ROOT=Path(__file__).resolve().parents[1]


def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8-sig'))


def main():
    aniso=read('01_PhysGaussian/docs/anisotropy-metrics.json');assert aniso['all_checks_passed']
    base=aniso['axis_ratios']['baseline'];reg=aniso['axis_ratios']['regularized']
    am=aniso['evaluation']['mean'];bm=aniso['baseline_evaluation']
    out=ROOT/'01_PhysGaussian/outputs/ficus_anisotropy'
    values=np.load(out/'axis_ratio_comparison.npz')
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
    for name in ('baseline','regularized'):
        data=np.sort(values[name]);ax.semilogx(data,np.arange(1,len(data)+1)/len(data),label=name)
    ax.axvline(5,color='gray',linestyle='--');ax.set(xlabel='Major/minor Gaussian scale ratio',ylabel='Empirical CDF');ax.legend()
    fig.savefig(out/'axis_ratios.png',dpi=160);plt.close(fig)
    resume_note=''
    if aniso.get('resumed_simulation_only'):
        resume_note='''首次模拟启动遇到旧Warp生成源码的ASCII编码错误，随后导入修复又暴露同名模块/命名空间包冲突；两次失败日志分别保存为 [编码失败](../logs/ficus-anisotropy-simulation-first-ascii-failure.log) 和 [导入失败](../logs/ficus-anisotropy-simulation-import-failure.log)。外部适配器先建立命名空间包，再优先从既有ASCII别名导入MPM叶模块。未修改上游或项目外文件。恢复时只执行模拟，保留已完成的训练、200视图渲染和评估；metrics中的计时仅对应恢复调用，未反推或虚构之前各阶段用时。[原训练参数](../outputs/ficus_anisotropy/adapter-protocol.json)。'''
    text=f'''# PhysGaussian 可选各向异性正则实验

按预先固定的 [协议](ANISOTROPY_PROTOCOL.md) 实现式(12)，r=5、λ=0.01；单独从头执行完整30,000步训练、200测试视图、原5秒/125帧模拟。上游文件未改，外部AST只在图像损失赋值处加入正则项；保存源文件哈希、适配行号与逐千步诊断。此为本地Ficus方法验证，不是原图8凳子及未公开参数的复现。

- 未正则化：{base['gaussians']:,} 个高斯；平均轴比 {base['mean']:.6g}，中位 {base['median']:.6g}，95分位 {base['percentile95']:.6g}，超过5的比例 {base['fraction_above5']*100:.3f}%。PSNR {bm['PSNR']:.6f} dB、SSIM {bm['SSIM']:.6f}、LPIPS {bm['LPIPS']:.6f}。
- 正则化：{reg['gaussians']:,} 个高斯；平均轴比 {reg['mean']:.6g}，中位 {reg['median']:.6g}，95分位 {reg['percentile95']:.6g}，超过5的比例 {reg['fraction_above5']*100:.3f}%。PSNR {am['PSNR']:.6f} dB、SSIM {am['SSIM']:.6f}、LPIPS {am['LPIPS']:.6f}。

正则项是软惩罚，不要求最大轴比严格≤5。密化与优化耦合使最终粒子数可变化；均值降低本身不证明动态视觉或物理质量提高。保持原测试集，不按这些结果重新选阈值、权重或检查点。梯度有限差分、已知值、尺度不变性检查见 [函数验收](anisotropy-function-check.json)。

{resume_note}

[全部指标和实际命令](anisotropy-metrics.json) · [轴比分布](../outputs/ficus_anisotropy/axis_ratios.png) · [测试图](../outputs/ficus_anisotropy/heldout_comparison.jpg) · [完整视频](../outputs/ficus_anisotropy_full/output.mp4) · [逐帧状态](../outputs/ficus_anisotropy_full/metrics.json)。训练模型哈希与模拟输入一致。
'''
    (ROOT/'01_PhysGaussian/docs/ANISOTROPY_RESULTS.md').write_text(text,encoding='utf-8')
    vib=read('03_NeuralSound/docs/vibration-paper-schedule-metrics.json')
    rad=read('03_NeuralSound/docs/radiation-paper-schedule-metrics.json')
    oldv=read('03_NeuralSound/docs/vibration-training-metrics.json');oldr=read('03_NeuralSound/docs/radiation-training-metrics.json')
    audit=read('03_NeuralSound/docs/paper-schedule-checkpoint-audit.json')
    export=read('03_NeuralSound/outputs/radiation_paper_schedule/all_test_predictions/export-metrics.json')
    assert audit['passed'] and export['passed'] and vib['training_completed'] and rad['training_completed']
    assert vib['epochs']==rad['epochs']==100 and rad['batch_size']==16
    errors=np.array([s['transfer_relative_L2'] for s in rad['test']['samples']])
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for task,ax in zip(('vibration','radiation'),axes):
        for tag,label in ((f'{task}_training','released optimizer profile'),(f'{task}_paper_schedule','paper optimizer profile')):
            history=read(f'03_NeuralSound/outputs/{tag}/history.json')
            ax.semilogy([r['epoch'] for r in history],[r['validation_loss'] for r in history],label=label)
        ax.set(title=task,xlabel='Epoch',ylabel='Validation loss');ax.legend()
    fig.savefig(ROOT/'03_NeuralSound/outputs/radiation_paper_schedule/optimizer_comparison.png',dpi=160);plt.close(fig)
    text=f'''# NeuralSound 正文优化器参数对照结果

依据论文PDF第7页 §6.2，两个网络均100轮，Adam初始lr=1e-4，每20轮减半；辐射batch16。完整训练已经结束，固定同一24几何及标签，验证集选择最佳模型，测试保持不变。此次是 [正文优化器参数对照](PAPER_SCHEDULE_PROTOCOL.md)，仍不是完整ABC数据、原论文架构或1/20子采样协议。

- 振动：正文参数最佳验证loss {vib['best_validation_loss']:.8g}，测试loss {vib['test']['mean_loss']:.8g}；旧公开代码参数200轮最佳验证loss {oldv['best_validation_loss']:.8g}，测试loss {oldv['test']['mean_loss']:.8g}。各对象三种初始化的原LOBPCG精修全部保存；准确性须用逐项残差判断，不能全部归因于网络。
- 辐射：正文参数最佳验证loss {rad['best_validation_loss']:.8g}，选中第 {export['selected_epoch']} 轮；24张测试FFAT相对L2均值 {errors.mean()*100:.3f}%，中位 {np.median(errors)*100:.3f}%，最大 {errors.max()*100:.3f}%。旧公开代码参数均值 {oldr['test']['mean_transfer_relative_L2']*100:.3f}%，旧失败结果完整保留。
- 本地声辐射每轮96张展开图，batch16产生6次更新、100轮600次；旧batch40每轮drop_last后80张/2次更新，共200次。batch、学习率和调度共同变化，不能把差异归因于某单一参数。振动仍逐轮使用全部16训练几何，非原文大数据每轮1/20采样。
- 新测试原始负幅值预测占 {export['negative_prediction_fraction']*100:.6f}%。误差按原始输出计算，全部预测对照图的共同色标也包含负值范围；没有用截断或单图归一化隐藏失败。
- 网络源码未改，CPU Adam公式沿用已验证版本。全部新checkpoint实际CPU读回并检查张量、完整状态、最终学习率/调度器与随机状态；全部24张预测由同一个冻结最佳checkpoint导出并重新计算误差一致。新结果不用于重新选择原模型或测试划分。

本次检查点全部写在项目NTFS目录，而旧正式实验使用Linux内部文件系统；计时包含不同I/O成本，不比较训练速度。即使数值改善，也不能推出完整ABC泛化或论文精度达标。

归一化测试预览和全部六页、24张物理幅值对照图均已目视检查。预测普遍有明显且相似的网格状纹理，未匹配BEM参考的平滑方向分布；共同色标还显示部分模态明显低估幅值、弱辐射模态出现高估。这是保存结果中的真实负现象；仅凭此现象不确定失败原因，不通过图像平滑或更换样本掩盖它。

[振动指标](vibration-paper-schedule-metrics.json) · [振动原始模态的独立FEM复核](paper-schedule-vibration-array-audit.json) · [辐射指标](radiation-paper-schedule-metrics.json) · [两种配置验证曲线](../outputs/radiation_paper_schedule/optimizer_comparison.png) · [全部预测](PAPER_SCHEDULE_PREDICTIONS.md) · [检查点验收](paper-schedule-checkpoint-audit.json)。
'''
    (ROOT/'03_NeuralSound/docs/PAPER_SCHEDULE_RESULTS.md').write_text(text,encoding='utf-8')
    records=[];lines=['# 非单位预旋转场景的完整 SH 坐标修复验证','',
        '在原模型、原完整配置和原物理求解器上，仅通过外部适配器将MPM逆旋转变换至世界坐标。原发布版结果保持。每帧在完全同一粒子状态、相机和光栅参数下另外渲染未修正颜色，避免把两次物理模拟差异误判为SH修复效果。',
        '逐帧差异由光栅器的浮点RGB输出计算；四个选定帧额外保存完整原始浮点图像对，并独立复算L2/平均绝对差/最大绝对差。PNG/MP4是量化后的观看版本，不能要求从8位图像逐比特重建这些浮点误差。','']
    for name in ('bread','plane','vasedeck'):
        tag=f'{name}_sh_corrected';m=read(f'01_PhysGaussian/outputs/{tag}/metrics.json')
        original=read(f'01_PhysGaussian/outputs/{name}_official_full/metrics.json')
        assert m['all_checks_passed'] and m['sh_frame_correction'] and m['model_sha256']==original['model_sha256']
        rows=m['sh_same_state_comparison'];assert len(rows)==m['rendered_frames']
        errors=np.array([r['relative_image_L2'] for r in rows]);assert np.isfinite(errors).all()
        folder=ROOT/f'01_PhysGaussian/outputs/{tag}/same_state_comparison'
        originals=sorted(folder.glob('*_original.png'));assert len(originals)==4
        canvas=Image.new('RGB',(1280,680),'white');draw=ImageDraw.Draw(canvas)
        for i,p in enumerate(originals):
            for row,suffix in enumerate(('original','corrected')):
                path=folder/p.name.replace('original',suffix)
                with Image.open(path) as im:
                    thumb=ImageOps.contain(im.convert('RGB'),(320,320));canvas.paste(thumb,(i*320+(320-thumb.width)//2,row*340+20))
                draw.text((i*320+5,row*340+3),p.stem.split('_original')[0]+' / '+suffix,fill='black')
        canvas.save(folder/'overview.jpg',quality=94)
        records.append(dict(scene=name,frames=len(rows),mean_relative_image_L2=float(errors.mean()),maximum_relative_image_L2=float(errors.max())))
        lines.extend([f'## {name}','',f'{len(rows)}帧；同状态修复前后图像相对L2均值 {errors.mean():.6g}，最大 {errors.max():.6g}。此数值是两种算法之差，不是相对真实图像的误差或修复收益。',
            f'[完整视频](../outputs/{tag}/output.mp4) · [同状态对照](../outputs/{tag}/same_state_comparison/overview.jpg) · [首个浮点图像对](../outputs/{tag}/same_state_comparison/frame_0001_raw.npz) · [指标](../outputs/{tag}/metrics.json)',''])
    lines+=['公式正确性由 [独立不变量实验](SH_FRAME_AUDIT.md) 验证。完整场景测试证明适配器实际接入原渲染链且输出有效，缺少动态真实图像时不宣称视觉指标提升。未重跑Q为单位阵的Ficus/Wolf以及默认无旋转的Pillow，因为该转换在这些情况下恒等。','']
    (ROOT/'01_PhysGaussian/docs/SH_CORRECTED_SCENES.md').write_text('\n'.join(lines),encoding='utf-8')
    (ROOT/'01_PhysGaussian/docs/sh-corrected-scenes-metrics.json').write_text(json.dumps(dict(execution_completed=True,records=records),indent=2))
    print('Completed extension reports generated.')


if __name__=='__main__':main()
