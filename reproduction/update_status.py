"""Current, artifact-based status; safe to run during long experiments."""
import json,re
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    lines=['# 当前复现状态','',f'更新时间：{datetime.now().astimezone().isoformat(timespec="minutes")}。本文件只按实际产物记录；脚本已准备不算实验完成。','',
        '## PhysGaussian','']
    for name in ('ficus_official_full','bread_official_full','pillow2sofa_official_full','plane_official_full','vasedeck_official_full','wolf_official_full','ficus_reconstruction','ficus_reconstructed_full','gaussian_transport','ficus_anisotropy','ficus_anisotropy_full','bread_sh_corrected','plane_sh_corrected','vasedeck_sh_corrected'):
        folder=ROOT/'01_PhysGaussian/outputs'/name;metrics=folder/'metrics.json'
        if metrics.exists():
            d=json.loads(metrics.read_text());result='通过保存结果检查' if d.get('all_checks_passed') else '结果需查看'
            lines.append(f'- {name}：{result}，[指标]({metrics.relative_to(ROOT).as_posix()})。')
        else:
            audit=folder/'frame-audit.json'
            count=len(json.loads(audit.read_text())) if audit.exists() else 0
            detail=f'；已保存 {count} 帧审计' if count else ''
            if name=='ficus_reconstruction':
                log=ROOT/'01_PhysGaussian/logs/ficus-reconstruction-train.log'
                if log.exists():
                    with log.open('rb') as f:
                        f.seek(max(0,log.stat().st_size-16384));tail=f.read().decode('utf-8',errors='replace')
                    steps=re.findall(r'(\d+)/30000',tail)
                    if steps:detail=f'；训练日志已到 {steps[-1]}/30000 步'
            lines.append(f'- {name}：尚无最终指标'+detail+'。')
    lines+=['','## PAT','']
    for name in ('pat_pipeline','pat_extended','moving_listener','modalsound_basis','modalsound_fem','modalsound_transfer'):
        path=ROOT/'02_PAT/outputs'/name/'metrics.json'
        lines.append(f'- {name}：'+('已有实际结果' if path.exists() else '待核查最终指标')+'。')
    lines+=['','## NeuralSound','']
    for name in ('official_fem','official_example','vibration_training','radiation_training','neural_audio','example_hybrid_ood','example_hybrid_ood_extended','example_acoustic_ood','vibration_paper_schedule','radiation_paper_schedule'):
        folder=ROOT/'03_NeuralSound/outputs'/name;metrics=folder/'metrics.json'
        if metrics.exists():lines.append(f'- {name}：已有实际最终结果，[指标]({metrics.relative_to(ROOT).as_posix()})；精度须按其中数值判读。')
        else:
            history=folder/'history.json'
            count=len(json.loads(history.read_text())) if history.exists() else 0
            lines.append(f'- {name}：尚无最终指标'+(f'；逐轮记录已到 {count} 轮' if count else '')+'。')
    benchmark=ROOT/'03_NeuralSound/docs/vibration-benchmark.json'
    lines+=['- 包含网络开销的振动计时：'+('已有最终结果。' if benchmark.exists() else '尚无最终结果。'),'',
        '## 记录与边界','',
        '- [继续执行记录](继续复现执行记录.md) 保存调度、适配和失败记录；其中标明的暂停进程需要按最新记录恢复。',
        '- [已完成振动网络报告](03_NeuralSound/docs/VIBRATION_RESULTS.md)、[官方完整场景](01_PhysGaussian/docs/OFFICIAL_SCENES.md)、[PAT 扩展](02_PAT/docs/EXTENDED_RESULTS.md)。',
        '- 最终报告在全部既定实验后由实际指标生成；当前总报告可能仍为归档前的基础阶段，不据此忽略新增产物。',
        '- 这些本地实验不自动等同于完整 ABC、原 PAT 复杂场景、论文全数据/速度复现。']
    if (ROOT/'reproduction/extended-artifact-audit.json').exists():
        audit=json.loads((ROOT/'reproduction/extended-artifact-audit.json').read_text())
        if audit.get('passed') and len(audit.get('checks',[]))>=31 and (ROOT/'reproduction/audit/final-acceptance.json').exists():
            lines=[line.replace('最终报告在全部既定实验后由实际指标生成；当前总报告可能仍为归档前的基础阶段，不据此忽略新增产物。',
                '既定扩展实验产物已通过独立验证；最终内容见 [复现总报告](复现总报告.md) 与 [验证记录](扩展产物验证记录.md)。').replace(
                '保存调度、适配和失败记录；其中标明的暂停进程需要按最新记录恢复。',
                '保存调度、适配和失败记录；早期暂停属于历史调度，最终运行状态见该文末尾。') for line in lines]
    (ROOT/'STATUS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':main()
