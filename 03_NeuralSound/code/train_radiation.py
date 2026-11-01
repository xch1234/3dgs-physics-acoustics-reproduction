"""Train the unmodified public AcousticNet on a documented small local split.

Real sparse-convolution network; not pretrained paper weights or ABC evaluation.
Uses the released dataset normalization and MSE objectives, batch size forty.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS','2')
import sys
import time
import json
import argparse
import shutil
from pathlib import Path
import numpy as np
import torch
import MinkowskiEngine as ME
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from torch.utils.data import Dataset,DataLoader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code/NeuralSound'))
from src.net.acousticnet import AcousticNet
from src.classic.bem.data_aug import random_rotate_mirror


class Maps(Dataset):
    def __init__(self,phase,augment=False,folder=None):
        folder=Path(folder or ROOT/'inputs/procedural_bempp')
        self.names=(folder/f'{phase}.txt').read_text().splitlines()
        self.data=[dict(np.load(folder/n)) for n in self.names]
        self.samples=[(i,j) for i,d in enumerate(self.data) for j in range(len(d['freqs']))]
        self.augment=augment
    def __len__(self):return len(self.samples)
    def __getitem__(self,index):
        i,j=self.samples[index];d=self.data[i];freq=d['freqs'][j]
        coords=d['coords'].copy()-1;vib=d['feats_in'][:,:,j].copy();code=d['surface'].copy()
        target=d['feats_out_far'][j][None].copy()
        if self.augment:coords,vib,target,code=random_rotate_mirror(coords,vib,target,code)
        rms=np.sqrt(np.mean(vib**2));vib=vib/rms;target=target/rms
        amplitude=np.sqrt(np.mean(target**2));target=target/amplitude
        k=2*np.pi*freq/343;kmin=2*np.pi*20/343;kmax=2*np.pi*20000/343
        trig=np.array([f(k*(.15/32)*scale) for scale in (.25,.5,1,2,4) for f in (np.cos,np.sin)])
        feats=np.c_[vib,code,np.full(len(coords),(k-kmin)/(kmax-kmin)),np.tile(trig,(len(coords),1)),(coords/16-1)/.5]
        return coords.astype(np.int32),feats.astype(np.float32),target.astype(np.float32),np.float32((np.log(amplitude)+8)/3),f'{self.names[i]}:{j}'


def collate(items):
    c,f,t,a,n=zip(*items)
    return ME.utils.batched_coordinates(c),torch.tensor(np.concatenate(f)),torch.tensor(np.stack(t)),torch.tensor(a)[:,None],n


def evaluate(net,loader,device,save=None):
    net.eval();records=[];losses=[];images=[]
    with torch.no_grad():
        for coords,feats,target,norm,names in loader:
            target=target.to(device);norm=norm.to(device)
            pred,pnorm=net(coords.to(device),feats.to(device))
            loss=((pred-target)**2).mean()+((pnorm-norm)**2).mean()
            losses.append(float(loss))
            for i,name in enumerate(names):
                truth=target[i]*torch.exp(norm[i]*3-8)
                estimate=pred[i]*torch.exp(pnorm[i]*3-8)
                records.append(dict(sample=name,normalized_map_relative_L2=float(torch.linalg.norm(pred[i]-target[i])/torch.linalg.norm(target[i])),
                    amplitude_log_error=float((pnorm[i]-norm[i])*3),transfer_relative_L2=float(torch.linalg.norm(estimate-truth)/torch.linalg.norm(truth))))
                if len(images)<4:images.append((target[i,0].cpu().numpy(),pred[i,0].cpu().numpy(),name))
    if save:
        fig,axs=plt.subplots(len(images),2,figsize=(8,2.5*len(images)),layout='constrained')
        for row,(a,b,name) in enumerate(images):
            for col,data in enumerate((a,b)):
                axs[row,col].imshow(data.T,origin='lower',vmin=0,vmax=max(a.max(),b.max()))
                axs[row,col].set_title(f'{name} '+('BEM target' if col==0 else 'AcousticNet'))
        fig.savefig(save,dpi=150);plt.close(fig)
    return dict(loss=float(np.mean(losses)),mean_transfer_relative_L2=float(np.mean([r['transfer_relative_L2'] for r in records])),samples=records)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--epochs',type=int,default=100)
    parser.add_argument('--batch-size',type=int,default=40);parser.add_argument('--optimizer',choices=['adam','cpu_adam','sgd'],default='adam')
    parser.add_argument('--cpu-threads',type=int,default=8)
    parser.add_argument('--paper-schedule',action='store_true',help='Separate local control using paper Sec.6.2 optimizer schedule; does not overwrite released-profile results')
    parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    if args.paper_schedule:
        if args.epochs!=100:parser.error('The paper schedule control is fixed to 100 epochs.')
        args.batch_size=16
    learning_rate=1e-4 if args.paper_schedule else 1e-3
    decay_period=20 if args.paper_schedule else 8
    decay_factor=.5 if args.paper_schedule else .8
    np.random.seed(20261102);torch.manual_seed(20261102);torch.cuda.manual_seed_all(20261102)
    torch.set_num_threads(args.cpu_threads);device='cuda:0'
    out=ROOT/'outputs'/('radiation_paper_schedule' if args.paper_schedule else 'radiation_training');out.mkdir(parents=True,exist_ok=True)
    checkpoint_dir=out/'checkpoints' if args.paper_schedule else Path('/opt/3dgs-runtime/checkpoints/neuralsound-radiation')
    if not args.resume and checkpoint_dir.exists() and (checkpoint_dir/'last.pt').exists():
        from datetime import datetime
        archive=checkpoint_dir.with_name(checkpoint_dir.name+'-previous-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        checkpoint_dir.rename(archive)
    checkpoint_dir.mkdir(parents=True,exist_ok=True)
    def save_checkpoint(payload,name):
        temporary=checkpoint_dir/(name+'.tmp')
        torch.save(payload,temporary);temporary.replace(checkpoint_dir/name)
    if args.resume and not (checkpoint_dir/'last.pt').exists() and (out/'last.pt').exists():
        for name in ('last.pt','best.pt'):
            shutil.copy2(out/name,checkpoint_dir/name)
    train=Maps('train',True);val=Maps('val');test=Maps('test')
    tr=DataLoader(train,batch_size=args.batch_size,shuffle=True,num_workers=0,collate_fn=collate,drop_last=True)
    va=DataLoader(val,batch_size=2,num_workers=0,collate_fn=collate)
    te=DataLoader(test,batch_size=2,num_workers=0,collate_fn=collate)
    net=AcousticNet(23).to(device)
    parameters=sum(p.numel() for p in net.parameters())
    print('AcousticNet parameters:',parameters,'GPU:',torch.cuda.get_device_name(),flush=True)
    free_bytes,_=torch.cuda.mem_get_info()
    if args.optimizer=='adam' and parameters*4*3>free_bytes*.85:
        print('Keeping the full architecture; placing Adam moments on CPU to fit VRAM.',flush=True)
        args.optimizer='cpu_adam'
    optimizer_check=None
    if args.optimizer=='cpu_adam':
        from cpu_adam import CPUAdam,validate_against_torch
        optimizer_check=validate_against_torch(device)
        optimizer=CPUAdam(net.parameters(),lr=learning_rate)
    elif args.optimizer=='adam':optimizer=torch.optim.Adam(net.parameters(),lr=learning_rate,foreach=False)
    else:optimizer=torch.optim.SGD(net.parameters(),lr=.01,momentum=.9)
    scheduler=torch.optim.lr_scheduler.StepLR(optimizer,step_size=decay_period,gamma=decay_factor)
    start_epoch=0;history=[];best=float('inf');started=time.perf_counter()
    if args.resume and (checkpoint_dir/'last.pt').exists():
        ck=torch.load(checkpoint_dir/'last.pt',map_location='cpu');net.load_state_dict(ck['model']);optimizer.load_state_dict(ck['optimizer'])
        scheduler.load_state_dict(ck['scheduler']);start_epoch=ck['epoch']+1;history=ck['history'];best=ck['best']
        if 'rng_numpy' in ck:
            np.random.set_state(ck['rng_numpy']);torch.set_rng_state(ck['rng_torch'])
            torch.cuda.set_rng_state_all(ck['rng_cuda'])
        del ck
    else:
        initial=evaluate(net,va,device)
        (out/'initial-validation.json').write_text(json.dumps(initial,indent=2))
    torch.cuda.reset_peak_memory_stats()
    for epoch in range(start_epoch,args.epochs):
        net.train();losses=[]
        for coords,feats,target,norm,_ in tr:
            optimizer.zero_grad(set_to_none=True)
            pred,pnorm=net(coords.to(device),feats.to(device))
            loss=((pred-target.to(device))**2).mean()+((pnorm-norm.to(device))**2).mean()
            if not torch.isfinite(loss):raise RuntimeError(f'Non-finite loss at epoch {epoch}')
            loss.backward();torch.nn.utils.clip_grad_norm_(net.parameters(),10);optimizer.step()
            losses.append(float(loss.detach()))
        score=evaluate(net,va,device);scheduler.step()
        entry=dict(epoch=epoch+1,train_loss=float(np.mean(losses)),validation_loss=score['loss'],validation_transfer_error=score['mean_transfer_relative_L2'],next_learning_rate=float(scheduler.get_last_lr()[0]))
        history.append(entry);print(entry,flush=True)
        if score['loss']<best:
            best=score['loss'];save_checkpoint(dict(model=optimizer.model_state_dict(net) if args.optimizer=='cpu_adam' else net.state_dict(),epoch=epoch,architecture='unmodified AcousticNet(23)',args=vars(args)),'best.pt')
        if (epoch+1)%5==0 or epoch+1==args.epochs:
            save_checkpoint(dict(model=optimizer.model_state_dict(net) if args.optimizer=='cpu_adam' else net.state_dict(),optimizer=optimizer.state_dict(),scheduler=scheduler.state_dict(),epoch=epoch,history=history,best=best,
                rng_numpy=np.random.get_state(),rng_torch=torch.get_rng_state(),rng_cuda=torch.cuda.get_rng_state_all()),'last.pt')
        (out/'history.json').write_text(json.dumps(history,indent=2))
    ck=torch.load(checkpoint_dir/'best.pt',map_location='cpu');net.load_state_dict(ck['model']);del ck
    result=evaluate(net,te,device,save=out/'test_maps.png')
    for name in ('best.pt','last.pt'):shutil.copy2(checkpoint_dir/name,out/name)
    initial=json.loads((out/'initial-validation.json').read_text())
    metrics=dict(scope='actual public NeuralSound radiation network trained on 24 local cuboids with audited released Bempp labels; not paper data or accuracy',
        training_completed=True,architecture='unmodified AcousticNet(23)',parameters=parameters,optimizer=args.optimizer,
        epochs=args.epochs,batch_size=args.batch_size,cpu_threads=args.cpu_threads,train_maps=len(train),validation_maps=len(val),test_maps=len(test),cpu_adam_max_difference_from_torch=optimizer_check,
        initial_validation_loss=initial['loss'],best_validation_loss=best,validation_improved=best<initial['loss'],
        test=result,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),elapsed_s=time.perf_counter()-started,
        resumed_from_epoch=start_epoch,elapsed_note='current invocation; previous interrupted segment excluded',
        checkpoint_policy='atomic best checkpoints; full state every five epochs and final; final best/last copied to output directory',
        protocol='paper Sec.6.2 optimizer-parameter control on unchanged local data/public architecture' if args.paper_schedule else 'released-code local profile',
        training_settings=dict(initial_learning_rate=learning_rate,decay_period=decay_period,decay_factor=decay_factor,batches_per_epoch=len(tr),parameter_updates=len(tr)*args.epochs),
        adaptations=['local geometry-disjoint dataset; released Bempp operators with double precision and Numba CPU backend',
            f'batch size {args.batch_size}; released setting is 40','gradient norm clipped at 10','fixed full-mode validation, best chosen only on validation'])
    metric_name='radiation-paper-schedule-metrics.json' if args.paper_schedule else 'radiation-training-metrics.json'
    payload=json.dumps(metrics,indent=2);(out/'metrics.json').write_text(payload);(ROOT/'docs'/metric_name).write_text(payload)
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
    ax.semilogy([r['epoch'] for r in history],[r['train_loss'] for r in history],label='Train')
    ax.semilogy([r['epoch'] for r in history],[r['validation_loss'] for r in history],label='Validation')
    ax.set(xlabel='Epoch',ylabel='Map MSE + normalized log-amplitude MSE',title='Public AcousticNet / local procedural split');ax.legend()
    fig.savefig(out/'learning_curve.png',dpi=160);plt.close(fig)
    print(payload,flush=True)


if __name__=='__main__':main()
