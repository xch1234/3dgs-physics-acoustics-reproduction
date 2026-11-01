"""Train the pinned upstream 3DGS on Ficus with a real held-out test set."""
import argparse,json,subprocess,sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT/'code/PhysGaussian/gaussian-splatting'


def main():
    p=argparse.ArgumentParser();p.add_argument('--iterations',type=int,default=30000)
    p.add_argument('--resume');p.add_argument('--skip-training',action='store_true');args=p.parse_args()
    source=ROOT/'inputs/nerf_synthetic_ficus';out=ROOT/'outputs/ficus_reconstruction';out.mkdir(parents=True,exist_ok=True)
    provenance=json.loads((ROOT/'docs/ficus-dataset-provenance.json').read_text())
    assert provenance['all_images_verified'] and provenance['frame_counts']['train']==100
    def run(stage,command):
        logfile=ROOT/'logs'/f'ficus-reconstruction-{stage}.log';start=time.perf_counter()
        print('START',stage,flush=True)
        with logfile.open('w') as log:subprocess.run(command,cwd=REPO,stdout=log,stderr=subprocess.STDOUT,check=True)
        return time.perf_counter()-start
    commands={};times={}
    if not args.skip_training:
        checkpoints=sorted(set([v for v in (7000,15000,args.iterations) if v<=args.iterations]))
        commands['train']=[sys.executable,'-u','train.py','-s',str(source),'-m',str(out),
            '--eval','--white_background','--data_device','cpu','--resolution','1','--iterations',str(args.iterations),
            '--port','6019','--test_iterations',str(args.iterations),'--save_iterations',*[str(v) for v in checkpoints],
            '--checkpoint_iterations',*[str(v) for v in checkpoints]]
        if args.resume:commands['train']+=['--start_checkpoint',str(Path(args.resume).resolve())]
        times['train']=run('train',commands['train'])
    commands['render']=[sys.executable,'-u','render.py','-m',str(out),'-s',str(source),
        '--eval','--white_background','--data_device','cpu','--resolution','1','--iteration',str(args.iterations),'--skip_train']
    times['render']=run('render',commands['render'])
    commands['evaluate']=[sys.executable,'-u',str(ROOT/'code/evaluate_reconstruction.py'),'--iteration',str(args.iterations)]
    times['evaluate']=run('evaluate',commands['evaluate'])
    evaluation=json.loads((out/'evaluation.json').read_text())
    ply=out/f'point_cloud/iteration_{args.iterations}/point_cloud.ply';assert ply.exists()
    metrics=dict(scope='upstream original 3DGS appearance training supporting PhysGaussian, not full paper benchmark',
        all_checks_passed=True,iterations=args.iterations,train_views=100,test_views=provenance['frame_counts']['test'],
        image_resolution=[800,800],white_background=True,eval_split=True,commands=commands,seconds=times,
        evaluation=evaluation,checkpoint_sha256=hashlib.sha256(ply.read_bytes()).hexdigest(),
        adaptations=['source images stored on CPU to conserve VRAM','streamed per-image official SSIM/PSNR/LPIPS evaluation'],
        provenance='ficus-dataset-provenance.json',
        caveat='published PhysGaussian Ficus cfg_args has eval=False; this newly trained checkpoint alone uses a held-out split')
    payload=json.dumps(metrics,indent=2);(out/'metrics.json').write_text(payload);(ROOT/'docs/reconstruction-metrics.json').write_text(payload)
    print(payload,flush=True)


if __name__=='__main__':main()
