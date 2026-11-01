"""Measure full public AcousticNet batch 40, including actual Adam update."""
import json,time
import numpy as np
import torch
from torch.utils.data import DataLoader
from train_radiation import ROOT,Maps,collate,AcousticNet
from cpu_adam import CPUAdam,validate_against_torch


def main():
    torch.set_num_threads(8);np.random.seed(20261102);torch.manual_seed(20261102)
    torch.cuda.reset_peak_memory_stats();started=time.perf_counter()
    report=dict(batch_size=40,architecture='unmodified AcousticNet(23)',optimizer='CPU master Adam',passed=False)
    try:
        report['adam_reference_difference']=validate_against_torch('cuda:0')
        net=AcousticNet(23).cuda().train();optimizer=CPUAdam(net.parameters(),lr=1e-3)
        loader=DataLoader(Maps('train',True),batch_size=40,shuffle=True,collate_fn=collate,num_workers=0)
        coords,feats,target,norm,_=next(iter(loader))
        pred,pnorm=net(coords.cuda(),feats.cuda())
        loss=((pred-target.cuda())**2).mean()+((pnorm-norm.cuda())**2).mean()
        assert torch.isfinite(loss)
        loss.backward();grad=torch.nn.utils.clip_grad_norm_(net.parameters(),10);assert torch.isfinite(grad)
        optimizer.step();torch.cuda.synchronize()
        report.update(passed=True,parameters=sum(p.numel() for p in net.parameters()),loss=float(loss),gradient_norm_before_clip=float(grad),
            input_voxels=len(feats),peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved(),
            elapsed_s=time.perf_counter()-started)
    except Exception as error:
        report.update(error=repr(error),peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),elapsed_s=time.perf_counter()-started)
    (ROOT/'docs/acoustic-batch40-probe.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
