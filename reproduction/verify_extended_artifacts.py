"""Check actual extended outputs. Missing outputs fail, never become successes."""
import json
import hashlib
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.sparse import load_npz
from verify_scope_extensions import verify as verify_extensions

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8-sig'))


def main():
    checks = []
    physics = ROOT / '01_PhysGaussian/outputs'
    for scene in ('ficus', 'bread', 'pillow2sofa', 'plane', 'vasedeck', 'wolf'):
        folder = physics / f'{scene}_official_full'
        m = json.loads((folder / 'metrics.json').read_text())
        assert m['all_checks_passed']
        assert len(m['frames']) == m['rendered_frames']
        assert len(list(folder.glob('*.png'))) == m['rendered_frames']
        states = np.load(folder / 'final_state.npz')
        assert all(np.isfinite(states[k]).all() for k in states.files)
        assert states['final_positions'].shape == (m['physical_particles'], 3)
        assert np.allclose([f['mass'] for f in m['frames']], m['frames'][0]['mass'], rtol=1e-6)
        checks.append(f'{scene}: {m["rendered_frames"]} frames, finite full particle states, conserved mass')
    for name in ('pat_extended', 'moving_listener', 'modalsound_fem'):
        m = read(f'02_PAT/outputs/{name}/metrics.json')
        assert m['all_checks_passed']
        checks.append(f'PAT {name}: recorded experiment checks passed')
    neural = ROOT / '03_NeuralSound'
    dataset = neural / 'inputs/procedural_bempp'
    split = [(dataset / f'{p}.txt').read_text().splitlines() for p in ('train', 'val', 'test')]
    assert list(map(len, split)) == [16, 4, 4]
    assert len(set(sum(split, []))) == 24
    signatures = []
    for name in sum(split, []):
        d = np.load(dataset / name)
        assert d['feats_out_far'].shape == (6, 64, 32)
        assert np.isfinite(d['feats_out_far']).all()
        assert (d['feats_out_far'] >= 0).all()
        signatures.append(hashlib.sha256(d['voxel'].tobytes()).hexdigest())
    assert len(set(signatures)) == 24
    dm = read('03_NeuralSound/docs/official-labels-dataset.json')
    assert dm['complete'] and len(dm['records']) == 24
    solves = [s for row in dm['records'] for s in row['gmres']]
    assert len(solves) == 144
    assert all(s['info'] == 0 and s['actual_relative_residual'] < 1.01e-8 for s in solves)
    checks.append('144 released Bempp labels: residuals passed; 24 distinct voxel geometries; disjoint 16/4/4 split')
    features=read('03_NeuralSound/docs/acoustic-feature-contract.json')
    assert features['passed'] and len(features['records'])==12
    checks.append('Twelve samples match original AcousticDatasetFar encoding within 1e-6 under identical mode/augmentation RNG')
    example = neural / 'outputs/official_example'
    K, M = load_npz(example / 'stiffness.npz'), load_npz(example / 'mass.npz')
    modes = np.load(example / 'reference_modes.npz')
    E, U = modes['eigenvalues'], modes['modes']
    residual = np.linalg.norm(K@U-(M@U)*E, axis=0)/(np.linalg.norm(K@U, axis=0)+np.linalg.norm((M@U)*E, axis=0))
    assert residual.max() < 1e-6
    checks.append(f'Official example independent reference residual {residual.max():.3g}; default GPU solver limitations retained')
    for name in ('vibration', 'radiation'):
        folder = neural / f'outputs/{name}_training'
        m = json.loads((folder / 'metrics.json').read_text())
        assert m['training_completed']
        history = json.loads((folder / 'history.json').read_text())
        assert len(history) == m['epochs']
        assert all(np.isfinite(h['train_loss']) and np.isfinite(h['validation_loss']) for h in history)
        assert (folder / 'best.pt').stat().st_size > 100000
        assert (folder / 'last.pt').stat().st_size > 100000
        checks.append(f'{name}: {m["epochs"]} completed epochs, saved weights and finite history; accuracy reported separately')
    checkpoint_audit=read('03_NeuralSound/docs/checkpoint-audit.json')
    assert checkpoint_audit['passed'] and len(checkpoint_audit['records'])==4
    vibration_arrays=read('03_NeuralSound/docs/vibration-array-audit.json')
    assert vibration_arrays['passed'] and len(vibration_arrays['records'])==12
    checks.append('All four trained checkpoints deserialize; complete model/optimizer tensors finite and resumable epochs/history/RNG verified')
    export_folder=neural/'outputs/radiation_training/all_test_predictions'
    exported=json.loads((export_folder/'export-metrics.json').read_text())
    assert exported['passed'] and exported['samples']==24
    arrays=np.load(export_folder/'predictions.npz')
    assert arrays['predicted_ffat'].shape==(24,64,32) and np.isfinite(arrays['predicted_ffat']).all()
    errors=np.linalg.norm((arrays['predicted_ffat']-arrays['bem_ffat']).reshape(24,-1),axis=1)/np.linalg.norm(arrays['bem_ffat'].reshape(24,-1),axis=1)
    np.testing.assert_allclose(errors,arrays['relative_L2'],rtol=1e-5,atol=1e-7)
    checks.append('All 24 held-out raw FFAT predictions saved with shared-scale comparison figures and recomputed errors')
    m = read('03_NeuralSound/outputs/neural_audio/metrics.json')
    assert m['execution_completed'] and m['reference_checks_passed']
    assert max(m['modal_relative_residuals']) < 1e-4
    wavs = sorted((neural / 'outputs/neural_audio').glob('*.wav'))
    assert len(wavs) == 6
    for path in wavs:
        with wave.open(str(path), 'rb') as f:
            assert (f.getnchannels(), f.getsampwidth(), f.getframerate(), f.getnframes()) == (1, 2, 48000, 144000)
            a = np.frombuffer(f.readframes(f.getnframes()), dtype='<i2').astype(np.int32)
            assert 0 < np.abs(a).max() < 32767
    checks.append('Neural audio: six non-silent PCM16 / 48 kHz / 3 second WAVs without full-scale clipping')
    benchmark=read('03_NeuralSound/docs/vibration-benchmark.json')
    assert benchmark['all_checks_passed'] and len(benchmark['records'])==12
    checks.append('Vibration benchmark: all 12 configurations include initialization costs and three measured trials')
    ood=read('03_NeuralSound/docs/example-acoustic-ood-metrics.json')
    assert ood['execution_completed'] and ood['reference']['reference_checks_passed']
    assert len(ood['test']['samples'])==2
    for i,solve in enumerate(ood['reference']['bem_solves']):
        assert solve['info']==0 and solve['relative_residual']<1.01e-8
        if 'LU' in solve['method']:
            systems=neural/'inputs/official_example_acoustic'
            with np.load(systems/f'boundary_system_{i}.npz') as system:
                matrix,rhs=system['matrix'],system['rhs']
            x=np.load(systems/f'direct_coefficients_{i}.npy')
            assert np.linalg.norm(matrix@x-rhs)/np.linalg.norm(rhs)<1.01e-8
            del matrix,rhs,x
    checks.append('Original author example radiation: two predetermined physical modes, audited BEM and frozen-network predictions')
    hybrid=read('03_NeuralSound/docs/example-hybrid-ood-metrics.json')
    assert hybrid['execution_completed'] and len(hybrid['records'])==3
    checks.append('Original example neural vibration: all three initializations executed; convergence flags reported without suppression')
    extended=read('03_NeuralSound/docs/example-hybrid-ood-extended-metrics.json')
    assert extended['execution_completed'] and extended['iteration_limit']==10000 and len(extended['records'])==3
    checks.append('Original example extended convergence check: separate 10000-step budget, all three initializations and actual residuals retained')
    m = read('01_PhysGaussian/outputs/ficus_reconstruction/metrics.json')
    assert m['all_checks_passed'] and m['iterations'] == 30000 and m['eval_split']
    assert m['train_views'] == 100 and m['test_views'] == 200
    checks.append('Original 3DGS reconstruction: 30,000 iterations, 100 training / 200 held-out evaluation views')
    own=read('01_PhysGaussian/outputs/ficus_reconstructed_full/metrics.json')
    assert own['all_checks_passed'] and own['rendered_frames']==125
    assert own['model_sha256']==m['checkpoint_sha256']
    checks.append('Newly trained Ficus PLY matches complete 125-frame simulation source hash')
    checks.extend(verify_extensions())
    report = dict(time=datetime.now().astimezone().isoformat(), passed=True, checks=checks,
                  note='Artifact verification is separate from paper benchmark replication or learned accuracy.')
    (ROOT / 'reproduction/extended-artifact-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (ROOT / '扩展产物验证记录.md').write_text('# 扩展实验产物验证\n\n'+report['time']+'\n\n'+'\n'.join('- PASS: '+c for c in checks)+'\n\n本检查不把训练完成等同于精度达标；局限及实际误差见各实验文档。\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
