"""Describe completed radiation metrics without tuning against test examples."""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    m = json.loads((ROOT/'outputs/radiation_training/metrics.json').read_text())
    history = json.loads((ROOT/'outputs/radiation_training/history.json').read_text())
    assert m['training_completed'] and len(history) == m['epochs']
    samples = m['test']['samples']
    errors = np.array([r['transfer_relative_L2'] for r in samples])
    best = min(history, key=lambda r:r['validation_loss'])
    rows = []
    for name in sorted({s['sample'].split(':')[0] for s in samples}):
        values = [s['transfer_relative_L2'] for s in samples if s['sample'].split(':')[0] == name]
        rows.append(f'- {name}：六图平均相对 L2 {np.mean(values)*100:.3f}%，最大 {max(values)*100:.3f}%。')
    text = f'''# 声辐射精度判读

正式原 batch {m['batch_size']} 训练 {m['epochs']} 轮，共 {m['epochs']*(m['train_maps']//m['batch_size'])} 次参数更新。只有 16 个训练几何；与作者相同 epoch 数并不代表相同样本量、更新次数或训练充分程度。完整 3.11 亿参数网络与原网络定义一致。

仅按验证损失选中第 {best['epoch']} 轮，最佳验证损失 {best['validation_loss']:.7g}。归一化图 MSE 与对数幅值 MSE 的训练目标，不等同于恢复幅值后的相对 FFAT 误差。

24 张独立测试图的 FFAT 相对 L2：算术平均 **{errors.mean()*100:.3f}%**，中位数 **{np.median(errors)*100:.3f}%**，最小 {errors.min()*100:.3f}%，最大 {errors.max()*100:.3f}%。

{chr(10).join(rows)}

已检查保存的测试图：预测方向细节不足，仍存在明显格状纹理。训练流程可以执行，但声辐射精度未达到可接受复现水平。不能用验证 loss 下降或音频可生成来掩盖此结论；也不根据已查看的测试误差重新选择 checkpoint。

相对误差在真值幅值较弱时可能被放大，但不能据此忽略失败样本。所有逐样本误差、幅值对数误差和归一化图误差见 [原始指标](radiation-training-metrics.json)。小几何族与有限更新量是明确的实验限制；本次没有通过消融证明它们是唯一原因。

[训练曲线](../outputs/radiation_training/learning_curve.png) · [固定顺序前四张测试图](../outputs/radiation_training/test_maps.png) · [训练协议](LOCAL_TRAINING_PROTOCOL.md)。未删去弱模态，未更换测试划分，未把本地权重称为作者预训练模型。
'''
    (ROOT/'docs/RADIATION_ACCURACY.md').write_text(text, encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
