"""Full separate Ficus reconstruction and simulation with Eq.(12)."""
import os
import sys
import json
import time
import argparse
import subprocess
import hashlib
from pathlib import Path
import numpy as np
from plyfile import PlyData

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT/'code/PhysGaussian/gaussian-splatting'


def ratios(ply):
    data=PlyData.read(str(ply))['vertex'].data
    logs=np.stack([data[f'scale_{i}'] for i in range(3)],axis=1)
    ratio=np.exp(logs.max(axis=1)-logs.min(axis=1)).astype(float)
    assert np.isfinite(ratio).all() and (ratio>=1).all()
    return ratio,dict(gaussians=len(ratio),mean=float(ratio.mean()),median=float(np.median(ratio)),
        percentile95=float(np.quantile(ratio,.95)),maximum=float(ratio.max()),fraction_above5=float(np.mean(ratio>5)))


def main():
    p=argparse.ArgumentParser();p.add_argument('--skip-training',action='store_true');p.add_argument('--resume')
    p.add_argument('--simulation-only',action='store_true',help='Use already completed 30000-step model and 200-view evaluation')
    args=p.parse_args()
    if args.simulation_only:args.skip_training=True
    out=ROOT/'outputs/ficus_anisotropy';out.mkdir(exist_ok=True)
    source=ROOT/'inputs/nerf_synthetic_ficus';start=time.perf_counter();commands={};timings={}
    def run(stage,script,arguments):
        command=[sys.executable,'-u',str(ROOT/'code/project_runtime.py'),str(script),*map(str,arguments)]
        commands[stage]=command;t=time.perf_counter();print('START',stage,flush=True)
        with (ROOT/'logs'/f'ficus-anisotropy-{stage}.log').open('w') as log:
            subprocess.run(command,cwd=REPO,stdout=log,stderr=subprocess.STDOUT,check=True)
        timings[stage]=time.perf_counter()-t
    if not args.skip_training:
        train_args=['--aniso-threshold',5,'--aniso-weight',.01,'-s',source,'-m',out,'--eval','--white_background',
            '--data_device','cpu','--resolution',1,'--iterations',30000,'--port',6019,'--test_iterations',30000,
            '--save_iterations',7000,15000,30000,'--checkpoint_iterations',7000,15000,30000]
        if args.resume:train_args+=['--start_checkpoint',Path(args.resume).resolve()]
        run('train',ROOT/'code/train_with_anisotropy.py',train_args)
    if not args.simulation_only:
        run('render',REPO/'render.py',['-s',source,'-m',out,'--eval','--white_background','--data_device','cpu',
            '--resolution',1,'--iteration',30000,'--skip_train'])
        run('evaluate',ROOT/'code/evaluate_reconstruction.py',['--output-dir',out,'--iteration',30000])
    else:
        assert json.loads((out/'anisotropy-history.json').read_text())[-1]['iteration']==30000
        assert len(list((out/'test/ours_30000/renders').glob('*.png')))==200
        assert (out/'chkpnt30000.pth').exists()
    ply=out/'point_cloud/iteration_30000/point_cloud.ply'
    base=ROOT/'outputs/ficus_reconstruction'
    regularized,rs=ratios(ply);baseline,bs=ratios(base/'point_cloud/iteration_30000/point_cloud.ply')
    evaluation=json.loads((out/'evaluation.json').read_text());base_eval=json.loads((base/'evaluation.json').read_text())
    assert evaluation['test_images']==200
    if args.simulation_only and (out/'axis_ratio_comparison.npz').exists():
        with np.load(out/'axis_ratio_comparison.npz') as saved:
            np.testing.assert_array_equal(saved['baseline'],baseline)
            np.testing.assert_array_equal(saved['regularized'],regularized)
    else:np.savez_compressed(out/'axis_ratio_comparison.npz',baseline=baseline,regularized=regularized)
    run('simulation',ROOT/'code/run_official_linux.py',['--model',out,'--config',ROOT/'code/PhysGaussian/config/ficus_config.json','--tag','ficus_anisotropy_full'])
    simulation=json.loads((ROOT/'outputs/ficus_anisotropy_full/metrics.json').read_text())
    model_sha=hashlib.sha256(ply.read_bytes()).hexdigest()
    assert simulation['all_checks_passed'] and simulation['rendered_frames']==125 and simulation['model_sha256']==model_sha
    result=dict(all_checks_passed=True,iterations=30000,train_views=100,test_views=200,threshold=5.,weight=.01,
        evaluation=evaluation,baseline_evaluation=base_eval['mean'],axis_ratios=dict(baseline=bs,regularized=rs),
        mean_ratio_reduced=rs['mean']<bs['mean'],checkpoint_sha256=model_sha,seconds=timings,commands=commands,
        total_elapsed_s=time.perf_counter()-start,simulation_frames=125,
        resumed_simulation_only=args.simulation_only,
        elapsed_note='Current invocation only; when simulation-only, original completed training/render/evaluation logs and files are preserved, their durations are not reconstructed.',
        scope='Local implementation of optional PhysGaussian Eq.(12); fixed r=5/lambda=.01, not paper Fig.8 settings or full benchmark')
    payload=json.dumps(result,indent=2);(out/'metrics.json').write_text(payload);(ROOT/'docs/anisotropy-metrics.json').write_text(payload)
    print(payload,flush=True)


if __name__=='__main__':main()
