"""Export every held-out prediction from the frozen validation-selected model."""
import hashlib
import json
import argparse
import numpy as np
import torch
from torch.utils.data import DataLoader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageOps
from train_radiation import ROOT, Maps, collate, AcousticNet


def main():
    p=argparse.ArgumentParser();p.add_argument('--paper-schedule',action='store_true');args=p.parse_args()
    torch.set_num_threads(2)
    torch.set_grad_enabled(False)
    folder=ROOT/'outputs'/('radiation_paper_schedule' if args.paper_schedule else 'radiation_training')
    out=folder/'all_test_predictions'
    out.mkdir(parents=True,exist_ok=True)
    weights=folder/'best.pt'
    net=AcousticNet(23).cuda().eval()
    ck=torch.load(weights,map_location='cpu')
    net.load_state_dict(ck['model'])
    selected_epoch=ck['epoch']+1
    del ck
    dataset=Maps('test',False)
    loader=DataLoader(dataset,batch_size=2,collate_fn=collate,num_workers=0)
    references=json.loads((folder/'metrics.json').read_text())['test']['samples']
    targets=[];predictions=[];normalized_targets=[];normalized_predictions=[];names=[];errors=[]
    for coords,features,target,amplitude,batch_names in loader:
        pred,pamp=net(coords.cuda(),features.cuda())
        for j,name in enumerate(batch_names):
            filename,mode=name.split(':');mode=int(mode)
            source=dataset.data[dataset.names.index(filename)]
            rms=np.sqrt(np.mean(source['feats_in'][:,:,mode]**2))
            truth=target[j,0].numpy()*float(torch.exp(amplitude[j]*3-8))*rms
            estimate=pred[j,0].cpu().numpy()*float(torch.exp(pamp[j]*3-8))*rms
            actual=float(np.linalg.norm(estimate-truth)/np.linalg.norm(truth))
            recorded=references[len(names)]
            assert recorded['sample']==name
            assert abs(actual-recorded['transfer_relative_L2'])<1e-4*(1+actual)
            names.append(name);targets.append(truth);predictions.append(estimate);errors.append(actual)
            normalized_targets.append(target[j,0].numpy());normalized_predictions.append(pred[j,0].cpu().numpy())
    np.savez_compressed(out/'predictions.npz',sample_names=np.array(names),
        bem_ffat=np.array(targets),predicted_ffat=np.array(predictions),
        normalized_bem=np.array(normalized_targets),normalized_prediction=np.array(normalized_predictions),
        relative_L2=np.array(errors))
    images=[]
    for first in range(0,len(names),4):
        fig,axs=plt.subplots(4,2,figsize=(8,10),layout='constrained')
        for j in range(4):
            index=first+j
            for col,data in enumerate((targets[index],predictions[index])):
                vmax=max(np.max(targets[index]),np.max(predictions[index]))
                vmin=min(0.,float(np.min(predictions[index]))) if args.paper_schedule else 0.
                mapped=axs[j,col].imshow(data.T,origin='lower',vmin=vmin,vmax=vmax)
                axs[j,col].set_title(names[index]+(' / BEM' if col==0 else ' / prediction'))
            if args.paper_schedule:
                fig.colorbar(mapped,ax=axs[j,:].tolist(),shrink=.8,format='%.1e')
        name=f'test_{first:02d}_{first+3:02d}.png';fig.savefig(out/name,dpi=150);plt.close(fig);images.append(name)
    overview=Image.new('RGB',(1200,1000),'white')
    for i,name in enumerate(images):
        with Image.open(out/name) as image:
            overview.paste(ImageOps.contain(image.convert('RGB'),(400,500)),((i%3)*400,(i//3)*500))
    overview.save(out/'overview.jpg',quality=92)
    digest=hashlib.sha256()
    with weights.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):digest.update(chunk)
    report=dict(passed=True,samples=len(names),selected_epoch=selected_epoch,checkpoint_sha256=digest.hexdigest(),
        all_errors_match_original_test=True,plots=images,
        negative_prediction_fraction=float(np.mean(np.array(predictions)<0)),
        units='far FFAT magnitude in original vibration feature scale; r times pressure/acceleration convention, not audio pressure',
        note='same frozen checkpoint; no model selection or tuning; raw negative outputs retained; each comparison pair shares its physical FFAT color scale')
    (out/'export-metrics.json').write_text(json.dumps(report,indent=2))
    lines=['# 全部独立测试预测','',
        f'保留第{selected_epoch}轮验证集选定的冻结权重，对24张独立测试图保存完整参考与原始预测数组。未调参或重新选择权重；重新计算误差与首次测试逐项一致。',
        '图中每一对参考/预测使用相同物理FFAT色标，幅值偏差不通过单独归一化隐藏；与训练报告中的归一化方向图含义不同。','',
        '[完整数组](../outputs/radiation_training/all_test_predictions/predictions.npz) · [权重哈希与检查记录](../outputs/radiation_training/all_test_predictions/export-metrics.json)','']
    lines+=['[全部24张图概览](../outputs/radiation_training/all_test_predictions/overview.jpg)','']
    lines.extend(f'- [样本 {i*4+1}–{i*4+4}](../outputs/radiation_training/all_test_predictions/{name})' for i,name in enumerate(images))
    name='PAPER_SCHEDULE_PREDICTIONS.md' if args.paper_schedule else 'ALL_TEST_PREDICTIONS.md'
    text='\n'.join(lines)+'\n'
    if args.paper_schedule:text=text.replace('outputs/radiation_training/','outputs/radiation_paper_schedule/')
    if args.paper_schedule:
        text+=f'\n原始负预测占 {report["negative_prediction_fraction"]*100:.6f}%；本组图像每对采用共同的最小/最大色标范围，负值也包含在显示范围中，没有把负预测截断后重新计算误差。\n'
    (ROOT/'docs'/name).write_text(text,encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
