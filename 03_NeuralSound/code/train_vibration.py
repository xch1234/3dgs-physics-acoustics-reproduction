"""Train official defaultUnet and run the released hybrid Rayleigh-Ritz/LOBPCG.

Local geometry-disjoint dataset, original residual-plus-eigenvalue objective.
Preserves the upstream network and solver files; saves actual trained weights.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS','2')
import sys
import argparse
import json
import time
from pathlib import Path
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];REPO=ROOT/'code/NeuralSound'
sys.path.insert(0,str(REPO));sys.path.insert(0,str(REPO/'vibration'))
import vibration.train as official
from src.net.eigennet import defaultUnet
from src.classic.fem.femModel import Hexahedron_model,Material
from src.classic.fem.project_util import voxel_to_edge
from src.classic.lobpcg import lobpcg


def load_samples(phase,device):
    folder=ROOT/'inputs/procedural_training';results=[]
    for name in (folder/f'{phase}.txt').read_text().splitlines():
        d=dict(np.load(folder/name));coords=torch.tensor(np.argwhere(d['voxel']),dtype=torch.int32)
        edge=torch.tensor(voxel_to_edge(d['voxel']),dtype=torch.long,device=device)
        vertices=int(edge.max())+1
        results.append(dict(name=name,data=d,coords=[coords],edge=edge,vertices=vertices,
            items=([coords],edge,[0,vertices],[name])))
    return results


def validation(samples):
    official.Config.net.eval();rows=[]
    with torch.no_grad(),torch.random.fork_rng(devices=[0]):
        for i,sample in enumerate(samples):
            torch.manual_seed(7000+i);torch.cuda.manual_seed_all(7000+i)
            err,E=official.forward_fun(sample['items'])
            rows.append(dict(sample=sample['name'],residual=float(err),mean_ritz_eigenvalue=float(E),loss=float(err+E)))
    return dict(mean_loss=float(np.mean([r['loss'] for r in rows])),samples=rows)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--epochs',type=int)
    parser.add_argument('--paper-schedule',action='store_true',help='Separate local control using paper Sec.6.2 optimizer schedule')
    parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    if args.epochs is None:args.epochs=100 if args.paper_schedule else 200
    if args.paper_schedule and args.epochs!=100:parser.error('The paper schedule control is fixed to 100 epochs.')
    np.random.seed(20261102);torch.manual_seed(20261102);torch.cuda.manual_seed_all(20261102)
    torch.set_num_threads(2);device='cuda:0';out=ROOT/'outputs'/('vibration_paper_schedule' if args.paper_schedule else 'vibration_training');out.mkdir(parents=True,exist_ok=True)
    official.device=torch.device(device);official.n=20;official.out_k=2
    official.Config.net=defaultUnet(24,48,linear=True).to(device)
    model=Hexahedron_model(mat=Material.Ceramic)
    Ke=torch.tensor(model._element_stiff_matrix,device=device,dtype=torch.float32)
    Me=torch.tensor(model._element_mass_matrix,device=device,dtype=torch.float32)
    official.stiff_e=Ke/torch.linalg.norm(Ke)/2;official.mass_e=Me/torch.linalg.norm(Me)/2
    train=load_samples('train',device);val=load_samples('val',device);test=load_samples('test',device)
    # Check the graph matvec against independent assembled FEM at matching material.
    example=train[0];physical=Hexahedron_model(example['data']['voxel'],Material.Ceramic)
    A=torch.tensor(physical.stiff_matrix.toarray(),device=device,dtype=torch.float32)/torch.linalg.norm(Ke)/2
    B=torch.tensor(physical.mass_matrix.toarray(),device=device,dtype=torch.float32)/torch.linalg.norm(Me)/2
    X=torch.randn(example['vertices']*3,3,device=device)
    a_error=float(torch.linalg.norm(official.A(X,example['edge'])-A@X)/torch.linalg.norm(A@X))
    b_error=float(torch.linalg.norm(official.B(X,example['edge'])-B@X)/torch.linalg.norm(B@X))
    assert a_error<1e-5 and b_error<1e-5,(a_error,b_error)
    del A,B,X
    optimizer=torch.optim.Adam(official.Config.net.parameters(),lr=1e-4,foreach=False)
    decay_period=20 if args.paper_schedule else 5
    decay_factor=.5 if args.paper_schedule else .8
    scheduler=torch.optim.lr_scheduler.StepLR(optimizer,step_size=decay_period,gamma=decay_factor)
    history=[];best=float('inf');start_epoch=0;started=time.perf_counter()
    if args.resume and (out/'last.pt').exists():
        ck=torch.load(out/'last.pt',map_location=device);official.Config.net.load_state_dict(ck['model'])
        optimizer.load_state_dict(ck['optimizer']);scheduler.load_state_dict(ck['scheduler'])
        history=ck['history'];best=ck['best'];start_epoch=ck['epoch']+1
        if 'rng_numpy' in ck:
            np.random.set_state(ck['rng_numpy']);torch.set_rng_state(ck['rng_torch'].cpu())
            torch.cuda.set_rng_state_all([s.cpu() for s in ck['rng_cuda']])
    else:
        torch.save(official.Config.net.state_dict(),out/'untrained.pt')
        (out/'initial-validation.json').write_text(json.dumps(validation(val),indent=2))
    torch.cuda.reset_peak_memory_stats()
    for epoch in range(start_epoch,args.epochs):
        official.Config.net.train();losses=[]
        for index in np.random.permutation(len(train)):
            optimizer.zero_grad(set_to_none=True)
            err,E=official.forward_fun(train[index]['items']);loss=err+E
            assert torch.isfinite(loss), (epoch,index,err,E)
            loss.backward()
            grad=torch.nn.utils.clip_grad_norm_(official.Config.net.parameters(),10)
            assert torch.isfinite(grad),(epoch,index,'gradient')
            optimizer.step();losses.append(float(loss.detach()))
        score=validation(val);scheduler.step()
        row=dict(epoch=epoch+1,train_loss=float(np.mean(losses)),validation_loss=score['mean_loss'],next_learning_rate=float(scheduler.get_last_lr()[0]));history.append(row)
        print(row,flush=True)
        if score['mean_loss']<best:
            best=score['mean_loss'];torch.save(official.Config.net.state_dict(),out/'best.pt')
        torch.save(dict(model=official.Config.net.state_dict(),optimizer=optimizer.state_dict(),scheduler=scheduler.state_dict(),epoch=epoch,history=history,best=best,
            rng_numpy=np.random.get_state(),rng_torch=torch.get_rng_state(),rng_cuda=torch.cuda.get_rng_state_all()),out/'last.pt')
        (out/'history.json').write_text(json.dumps(history,indent=2))
    official.Config.net.load_state_dict(torch.load(out/'best.pt',map_location=device));test_score=validation(test)
    refined=[]
    for sample_idx,sample in enumerate(test):
        physical=Hexahedron_model(sample['data']['voxel'],Material.Ceramic)
        scaleK=float(torch.linalg.norm(Ke))*2;scaleM=float(torch.linalg.norm(Me))*2
        A=torch.tensor(physical.stiff_matrix.toarray()/scaleK,device=device,dtype=torch.float64)
        B=torch.tensor(physical.mass_matrix.toarray()/scaleM,device=device,dtype=torch.float64)
        from scipy.linalg import eigh
        reference=eigh(A.cpu().numpy(),B.cpu().numpy(),subset_by_index=(0,19),eigvals_only=True)
        for method in ('random','untrained_network','trained_network'):
            torch.manual_seed(9000+sample_idx);torch.cuda.manual_seed_all(9000+sample_idx)
            x0=torch.randn(sample['vertices']*3,20,device=device)
            with torch.no_grad():
                if method!='random':
                    official.Config.net.load_state_dict(torch.load(out/('best.pt' if method=='trained_network' else 'untrained.pt'),map_location=device))
                    official.Config.net.eval()
                    predicted=official.net(sample['coords'],x0,sample['edge'])
                    x0,_=official.get_svqb(torch.cat((x0,predicted),dim=1),sample['edge'])
                history_refine=[]
                def tracker(worker):
                    if 'rerr' in worker.tvars:
                        history_refine.append(dict(step=int(worker.ivars.get('istep',0)),max_residual=float(worker.tvars['rerr'].max())))
                start=time.perf_counter()
                E,U=lobpcg(A,k=20,B=B,X=x0.double(),niter=2000,tol=1e-10,largest=False,tracker=tracker)
                torch.cuda.synchronize();elapsed=time.perf_counter()-start
                eigen_error=float(np.max(np.abs(E[6:12].cpu().numpy()-reference[6:12])/reference[6:12]))
                residual=float(torch.linalg.norm(A@U-B@U*E)/(
                    torch.linalg.norm(A@U)+torch.linalg.norm(B@U*E)))
                entry=dict(sample=sample['name'],initialization=method,iterations=len(history_refine),
                    first_six_elastic_eigenvalue_max_relative_error=eigen_error,relative_residual=residual,
                    seconds=elapsed,trace=history_refine)
                refined.append(entry);print('REFINEMENT',sample['name'],method,eigen_error,residual,elapsed,flush=True)
                np.savez_compressed(out/f'{Path(sample["name"]).stem}_{method}.npz',eigenvalues=E.cpu().numpy(),modes=U.cpu().numpy(),reference=reference)
    initial=json.loads((out/'initial-validation.json').read_text())
    metrics=dict(scope='official defaultUnet + released Rayleigh-Ritz and LOBPCG on local cuboids; not paper data/performance',
        training_completed=True,epochs=args.epochs,initial_validation_loss=initial['mean_loss'],best_validation_loss=best,
        protocol='paper Sec.6.2 optimizer-parameter control on unchanged local data/public architecture' if args.paper_schedule else 'released-code local profile',
        training_settings=dict(initial_learning_rate=1e-4,decay_period=decay_period,decay_factor=decay_factor,parameter_updates=len(train)*args.epochs),
        validation_improved=best<initial['mean_loss'],test=test_score,graph_A_relative_error=a_error,graph_B_relative_error=b_error,
        refinement=refined,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),elapsed_s=time.perf_counter()-started,
        adaptations=['24 local cuboids, split by geometry','gradient clipping at 10','fixed validation random seeds','double precision final refinement for independent verification'])
    metric_name='vibration-paper-schedule-metrics.json' if args.paper_schedule else 'vibration-training-metrics.json'
    payload=json.dumps(metrics,indent=2);(out/'metrics.json').write_text(payload);(ROOT/'docs'/metric_name).write_text(payload)
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
    for key in ('train_loss','validation_loss'):ax.semilogy([r['epoch'] for r in history],[r[key] for r in history],label=key)
    ax.set(xlabel='Epoch',ylabel='Residual + mean Ritz eigenvalue',title='Official defaultUnet / local procedural split');ax.legend()
    fig.savefig(out/'learning_curve.png',dpi=160);plt.close(fig)


if __name__=='__main__':main()
