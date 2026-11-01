"""Fresh inference with independent raw feature encoding of all held-out maps."""
import sys,json,gc,argparse
from common import ROOT,AUDIT,save,digest
sys.path.insert(0,str(ROOT/'verification_20261101'))
from neural_inference import encoded
import numpy as np
import torch,MinkowskiEngine as ME
from src.net.acousticnet import AcousticNet
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
torch.set_grad_enabled(False);torch.set_num_threads(2)
parser=argparse.ArgumentParser();parser.add_argument('--namespace',default='neural');parser.add_argument('--profiles',nargs='+',default=['radiation_released_profile','radiation_paper_schedule','radiation_longer']);args=parser.parse_args()
folder=ROOT/'03_NeuralSound/inputs/procedural_bempp';samples=[]
for name in (folder/'test.txt').read_text().splitlines():
 data=dict(np.load(folder/name))
 for mode in range(len(data['freqs'])):samples.append((name,mode,data))
assert len(samples)==24
summary=[]
for tag in args.profiles:
 source=AUDIT/'neural/outputs'/tag;out=AUDIT/args.namespace/'evaluations'/tag;out.mkdir(parents=True,exist_ok=True)
 if not (source/'metrics.json').exists():
  summary.append(dict(tag=tag,status='not verified',reason='training did not finish'));continue
 net=AcousticNet(23).cuda().eval();ck=torch.load(source/'best.pt',map_location='cpu');net.load_state_dict(ck['model']);epoch=ck['epoch']+1;del ck
 hist=json.loads((source/'history.json').read_text());best=min(hist,key=lambda r:r['validation_loss']);assert best['epoch']==epoch
 predicted=[];reference=[];names=[];map_errors=[];log_errors=[]
 for begin in range(0,len(samples),2):
  batch=samples[begin:begin+2];items=[encoded(d,m) for _,m,d in batch]
  coords=ME.utils.batched_coordinates([r[0] for r in items]).cuda();feats=torch.tensor(np.concatenate([r[1] for r in items]),device='cuda')
  p,a=net(coords,feats)
  for j,(name,mode,d) in enumerate(batch):
   raw=d['feats_out_far'][mode];rms=np.sqrt(np.mean(raw.astype(float)**2));normalized=p[j,0].cpu().numpy();logamp=float(a[j,0])*3-8
   predicted.append(normalized*np.exp(logamp)*items[j][2]);reference.append(raw);names.append(name+':'+str(mode))
   map_errors.append(float(np.mean((normalized-raw/rms)**2)));log_errors.append(logamp+np.log(items[j][2])-np.log(rms))
 p=np.array(predicted);r=np.array(reference);errors=np.linalg.norm((p-r).reshape(24,-1),axis=1)/np.linalg.norm(r.reshape(24,-1),axis=1)
 training=json.loads((source/'metrics.json').read_text());old=training['test']['samples']
 assert names==[x['sample'] for x in old];np.testing.assert_allclose(errors,[x['transfer_relative_L2'] for x in old],rtol=2e-4,atol=1e-5)
 np.savez_compressed(out/'predictions.npz',sample_names=names,predicted=p,reference=r,relative_L2=errors)
 result=dict(tag=tag,inference_completed=True,selected_epoch=epoch,selection='minimum validation loss only',checkpoint_sha256=digest(source/'best.pt'),mean_relative_L2=float(errors.mean()),median_relative_L2=float(np.median(errors)),maximum_relative_L2=float(errors.max()),global_relative_L2=float(np.linalg.norm(p-r)/np.linalg.norm(r)),normalized_map_MSE=float(np.mean(map_errors)),natural_log_amplitude_MSE=float(np.mean(np.square(log_errors))),negative_fraction=float((p<0).mean()),below_zero_predictor=bool(errors.mean()<1),all_maps_below_10percent=bool(np.all(errors<.1)),errors=errors.tolist(),samples=names,scope='Independent local evaluation on unchanged held-out 4 geometries / 24 maps; neither threshold is the paper Table 5 benchmark.')
 (out/'metrics.json').write_text(json.dumps(result,indent=2));summary.append(result)
 for first in range(0,24,4):
  fig,axes=plt.subplots(4,2,figsize=(9,10),layout='constrained')
  for j in range(4):
   i=first+j;lo=min(0,float(p[i].min()));hi=max(float(p[i].max()),float(r[i].max()))
   for col,array in enumerate((r[i],p[i])):
    im=axes[j,col].imshow(array.T,origin='lower',vmin=lo,vmax=hi);axes[j,col].set_title(names[i]+(' BEM' if col==0 else f' Network / error {errors[i]:.1%}'))
   fig.colorbar(im,ax=axes[j,:].tolist(),shrink=.75)
  fig.savefig(out/f'comparison_{first:02d}.png',dpi=120);plt.close(fig)
 selected=np.argsort(errors)[[0,len(errors)//2,-1]]
 fig,axes=plt.subplots(3,4,figsize=(15,8),layout='constrained')
 for row,i in enumerate(selected):
  rr=r[i]/np.sqrt(np.mean(r[i]**2));pp=p[i]/max(np.sqrt(np.mean(p[i]**2)),1e-30)
  arrays=[r[i],p[i],rr,pp]
  for col,a in enumerate(arrays):
   pair=arrays[0:2] if col<2 else arrays[2:4];lo=min(0,min(float(v.min()) for v in pair));hi=max(float(v.max()) for v in pair)
   im=axes[row,col].imshow(a.T,origin='lower',vmin=lo,vmax=hi)
   axes[row,col].set_title(['BEM / raw amplitude','Network / raw amplitude','BEM / unit RMS shape','Network / unit RMS shape'][col],fontsize=9)
   if col==0:axes[row,col].set_ylabel(names[i]+f'\nraw error {errors[i]:.1%}')
   if col in (1,3):fig.colorbar(im,ax=axes[row,col-1:col+1].tolist(),shrink=.7)
 fig.suptitle('Best / median / worst held-out maps. Right pair removes amplitude ONLY to inspect shape.')
 fig.savefig(out/'shape_and_amplitude.png',dpi=140);plt.close(fig)
 del net;gc.collect();torch.cuda.empty_cache();print(result,flush=True)
save('checks/V26-independent'+('' if args.namespace=='neural' else '-'+args.namespace)+'.json',summary)
