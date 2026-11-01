"""Independent feature encoding and frozen-network prediction; no optimizer or training writes."""
import sys,gc,json
import numpy as np
from common import ROOT,AUDIT,save,digest
sys.path.insert(0,str(ROOT/'03_NeuralSound/code/NeuralSound'))
import torch,MinkowskiEngine as ME
from src.net.acousticnet import AcousticNet
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def encoded(data,mode):
    coord=data['coords'].astype(np.int32)-1;vib=data['feats_in'][:,:,mode].astype(np.float64);rms=np.sqrt(np.mean(vib*vib));k=2*np.pi*data['freqs'][mode]/343
    periodic=np.ravel(np.column_stack([np.cos(k*.15/32*np.array([.25,.5,1,2,4])),np.sin(k*.15/32*np.array([.25,.5,1,2,4]))]))
    frequency=np.full((len(coord),1),(k-2*np.pi*20/343)/(2*np.pi*(20000-20)/343))
    features=np.column_stack([vib/rms,data['surface'],frequency,np.broadcast_to(periodic,(len(coord),10)),coord/8-2]).astype(np.float32)
    assert features.shape[1]==23
    return coord,features,float(rms)

def main():
    torch.set_num_threads(2);torch.set_grad_enabled(False)
    datafolder=ROOT/'03_NeuralSound/inputs/procedural_bempp';names=(datafolder/'test.txt').read_text().splitlines();samples=[]
    for name in names:
        with np.load(datafolder/name) as f:data={k:f[k] for k in f.files}
        for mode in range(len(data['freqs'])):samples.append((name,mode,data))
    assert len(samples)==24
    for tag in ('radiation_training','radiation_paper_schedule'):
        folder=ROOT/'03_NeuralSound/outputs'/tag;out=AUDIT/'neural'/tag;out.mkdir(parents=True,exist_ok=True)
        net=AcousticNet(23).cuda().eval();checkpoint=torch.load(folder/'best.pt',map_location='cpu');net.load_state_dict(checkpoint['model']);epoch=checkpoint['epoch']+1;del checkpoint
        predall=[];truthall=[];sample_names=[];map_mses=[];log_norm_errors=[]
        for begin in range(0,24,2):
            subset=samples[begin:begin+2];items=[encoded(d,mode) for _,mode,d in subset]
            coords=ME.utils.batched_coordinates([x[0] for x in items]).cuda();feats=torch.from_numpy(np.concatenate([x[1] for x in items])).cuda()
            pred,amp=net(coords,feats)
            for j,(name,mode,d) in enumerate(subset):
                prediction=pred[j,0].cpu().numpy()*np.exp(float(amp[j,0])*3-8)*items[j][2]
                predall.append(prediction);truthall.append(d['feats_out_far'][mode]);sample_names.append(name+':'+str(mode))
                reference_rms=np.sqrt(np.mean(d['feats_out_far'][mode].astype(float)**2))
                map_mses.append(float(np.mean((pred[j,0].cpu().numpy()-d['feats_out_far'][mode]/reference_rms)**2)))
                log_norm_errors.append(float(float(amp[j,0])*3-8+np.log(items[j][2])-np.log(reference_rms)))
            print(tag,begin+2,flush=True)
        prediction=np.array(predall);truth=np.array(truthall);err=np.linalg.norm((prediction-truth).reshape(24,-1),axis=1)/np.linalg.norm(truth.reshape(24,-1),axis=1)
        with np.load(folder/'all_test_predictions/predictions.npz') as old:
            np.testing.assert_array_equal(sample_names,old['sample_names'])
            delta=float(np.linalg.norm(prediction-old['predicted_ffat'])/np.linalg.norm(old['predicted_ffat']))
            assert delta<1e-4,delta
            np.testing.assert_allclose(err,old['relative_L2'],rtol=2e-4,atol=1e-6)
        np.savez_compressed(out/'predictions.npz',sample_names=sample_names,predicted=prediction,reference=truth,relative_L2=err)
        save('neural/'+tag+'/metrics.json',dict(inference_completed=True,selected_epoch=epoch,checkpoint_sha256=digest(folder/'best.pt'),mean_relative_L2=float(err.mean()),median_relative_L2=float(np.median(err)),max_relative_L2=float(err.max()),negative_fraction=float((prediction<0).mean()),normalized_map_MSE=float(np.mean(map_mses)),natural_log_amplitude_MSE=float(np.mean(np.array(log_norm_errors)**2)),new_vs_old_prediction_relative_L2=delta,samples=24,encoding='Independently encoded 23 channels directly from raw NPZ; no Maps or old export function used',errors=err.tolist(),metric_caution='Paper Table 5 uses normalized-map MSE and log-norm MSE, not raw relative L2; local 24 maps differ from its 100 test objects and 20 modes.'))
        for first in range(0,24,4):
            fig,axes=plt.subplots(4,2,figsize=(9,10),layout='constrained')
            for j in range(4):
                i=first+j;lo=min(0,float(prediction[i].min()));hi=max(float(truth[i].max()),float(prediction[i].max()))
                for col,a in enumerate((truth[i],prediction[i])):
                    im=axes[j,col].imshow(a.T,origin='lower',vmin=lo,vmax=hi);axes[j,col].set_title(sample_names[i]+(' / BEM' if col==0 else ' / fresh inference'))
                fig.colorbar(im,ax=axes[j,:].tolist(),shrink=.8)
            fig.savefig(out/f'comparison_{first:02d}.png',dpi=120);plt.close(fig)
        del net;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()
