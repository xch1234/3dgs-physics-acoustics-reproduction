"""Saved trained hybrid modes -> actual AcousticNet -> modal pressure audio.

Predetermined held-out box_21. A uniform 0.01 stiffness scaling of the Ceramic
FEM keeps all six acoustic frequencies in the local radiation training range.
This is an explicitly synthetic material, not identified real ceramic.
Exports the exact vertices, modal coordinates and impulse for same-object
rendering experiments; this does not change the magnitude-only audio method.
"""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[key]='2'
import sys,json,time,hashlib
from pathlib import Path
import numpy as np
for key,value in {'bool':bool,'int':int,'float':float,'complex':complex}.items():
    if key not in np.__dict__:setattr(np,key,value)
import torch
from scipy.io import wavfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'code/NeuralSound'))
import bempp.api.linalg
from bempp.api.operators import boundary,potential
from src.classic.bem import ffat
from src.classic.bem.util import boundary_voxel,boundary_encode
from src.classic.fem.femModel import Hexahedron_model,Material
from src.classic.fem.util import vertex_to_voxel_matrix
from train_radiation import Maps,collate,AcousticNet


def main():
    torch.set_grad_enabled(False);torch.set_num_threads(2)
    out=ROOT/'outputs/neural_audio';out.mkdir(parents=True,exist_ok=True)
    inputs=ROOT/'inputs/neural_audio';inputs.mkdir(parents=True,exist_ok=True)
    sample='box_21.npz';source=ROOT/'inputs/procedural_bempp'/sample
    d=dict(np.load(source));modal_path=ROOT/'outputs/vibration_training/box_21_trained_network.npz'
    hybrid=dict(np.load(modal_path));model=Hexahedron_model(d['voxel'],Material.Ceramic)
    K=model.stiff_matrix.tocsc()*.01;M=model.mass_matrix.tocsc()
    U=hybrid['modes'][:,6:12].copy();U/=np.sqrt(np.sum(U*(M@U),axis=0))
    E=np.sum(U*(K@U),axis=0);frequencies=np.sqrt(E)/(2*np.pi)
    residual=np.linalg.norm(K@U-(M@U)*E,axis=0)/(np.linalg.norm(K@U,axis=0)+np.linalg.norm((M@U)*E,axis=0))
    assert residual.max()<1e-4,(residual,frequencies)
    assert frequencies.min()>300 and frequencies.max()<6000,frequencies
    coords=np.argwhere(d['voxel']);surface,index=map(np.asarray,boundary_voxel(coords))
    vib=(vertex_to_voxel_matrix(d['voxel'])@U.reshape(-1,18)).reshape(len(coords),3,6)
    original_boundary=ffat.voxel2boundary
    def integer_boundary(*a,**kw):
        v,f,i=original_boundary(*a,**kw)
        return np.asarray(v),np.asarray(f,dtype=np.int64),np.asarray(i,dtype=np.int64)
    ffat.voxel2boundary=integer_boundary
    for module,names in ((boundary.helmholtz,('adjoint_double_layer','hypersingular')),
                         (boundary.sparse,('identity',)),(potential.helmholtz,('single_layer','double_layer'))):
        for name in names:
            original=getattr(module,name)
            def cpu_double(*a,_original=original,**kw):
                kw['device_interface']='numba';kw['precision']='double';return _original(*a,**kw)
            setattr(module,name,cpu_double)
    original_gmres=bempp.api.linalg.gmres;solves=[]
    def checked_gmres(A,b,**kw):
        kw['tol']=1e-8;result=original_gmres(A,b,**kw);rhs=b.projections(A.dual_to_range)
        r=float(np.linalg.norm(A.weak_form()@result[0].coefficients-rhs)/np.linalg.norm(rhs))
        assert result[1]==0 and r<1.01e-8,(result[1],r)
        solves.append(dict(info=int(result[1]),relative_residual=r));return result
    bempp.api.linalg.gmres=checked_gmres
    start=time.perf_counter();near,far=ffat.vibration_to_ffat(coords,vib,frequencies)
    bem_seconds=time.perf_counter()-start
    np.savez_compressed(inputs/sample,coords=surface,feats_in=vib[index],surface=np.asarray(boundary_encode(surface)),
        feats_out=near,feats_out_far=far,freqs=frequencies)
    (inputs/'test.txt').write_text(sample+'\n')
    dataset=Maps('test',False,inputs);network=AcousticNet(23).cuda().eval()
    weights=ROOT/'outputs/radiation_training/best.pt';ck=torch.load(weights,map_location='cpu');network.load_state_dict(ck['model']);del ck
    predictions=[];start=time.perf_counter();torch.cuda.reset_peak_memory_stats()
    for j in range(6):
        c,f,_,_,_=collate([dataset[j]])
        normalized,amplitude=network(c.cuda(),f.cuda())
        rms=np.sqrt(np.mean(vib[index,:,j]**2))
        prediction=normalized[0,0].cpu().numpy()*float(torch.exp(amplitude[0]*3-8))*rms
        predictions.append(prediction)
    torch.cuda.synchronize();inference_seconds=time.perf_counter()-start
    predictions=np.asarray(predictions);negative_fraction=float(np.mean(predictions<0))
    map_error=np.linalg.norm((predictions-far).reshape(6,-1),axis=1)/np.linalg.norm(far.reshape(6,-1),axis=1)
    # Unconstrained output regression can yield negative values; record the
    # fraction, then clamp only for a physically nonnegative magnitude in audio.
    magnitude=np.maximum(predictions,0)
    listener_indices=[(0,15),(16,15),(32,8)];radius=.3
    omega=np.sqrt(E);alpha,beta=6.,1e-7;decay=.5*(alpha+beta*E);wd=np.sqrt(E-decay**2)
    hit=int(np.argmax(model.vertices@np.array([1,.1,.01])))
    impulse=U.reshape(-1,3,6)[hit].T@np.array([0.,.8,.6])*1e-4
    fs=48000;t=np.arange(3*fs)/fs
    q=impulse[:,None]/wd[:,None]*np.exp(-decay[:,None]*t)*np.sin(wd[:,None]*t)
    ref=np.array([far[:,a,b]*E/radius for a,b in listener_indices])@q
    pred=np.array([magnitude[:,a,b]*E/radius for a,b in listener_indices])@q
    assert np.isfinite(ref).all() and np.isfinite(pred).all()
    gain=.85/max(np.abs(ref).max(),np.abs(pred).max());fade=np.ones(len(t));fade[-960:]=np.linspace(1,0,960)
    for name,waves in [('bem',ref),('neural',pred)]:
        for j,wave in enumerate(waves):wavfile.write(out/f'{name}_listener_{j+1}.wav',fs,np.rint(wave*gain*fade*32767).astype(np.int16))
    np.savez_compressed(out/'raw.npz',time_s=t,bem_pressure_Pa=ref,neural_pressure_Pa=pred,common_gain=gain,
        frequencies_Hz=frequencies,modes_mass_normalized=U,bem_ffat=far,neural_ffat=predictions,
        vertices_m=model.vertices,voxel=d['voxel'],modal_q=q,modal_impulse=impulse,
        rayleigh_alpha=alpha,rayleigh_beta=beta,hit_vertex=hit,impulse_direction=np.array([0.,.8,.6]),impulse_Ns=1e-4)
    metrics=dict(scope='trained official hybrid modal output -> trained official AcousticNet -> local modal pressure audio',
        execution_completed=True,reference_checks_passed=True,sample=sample,held_out_geometry=True,
        material=dict(density=2700,young_modulus_Pa=7.2e8,poisson_ratio=.19,rayleigh_alpha=alpha,rayleigh_beta=beta),
        material_note='0.01 stiffness-scaled Ceramic FEM for controlled in-range demonstration; not measured ceramic',
        frequencies_Hz=frequencies.tolist(),modal_relative_residuals=residual.tolist(),bem_solves=solves,
        per_mode_ffat_relative_L2=map_error.tolist(),negative_prediction_fraction=negative_fraction,
        per_listener_audio_relative_L2=(np.linalg.norm(pred-ref,axis=1)/np.linalg.norm(ref,axis=1)).tolist(),
        bem_seconds=bem_seconds,network_six_map_seconds=inference_seconds,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
        modal_artifact_sha256=hashlib.sha256(modal_path.read_bytes()).hexdigest(),radiation_checkpoint_sha256=hashlib.sha256(weights.read_bytes()).hexdigest(),
        limits=['six elastic modes; no rigid-body motion/collision engine','far FFAT magnitude divided by distance; no phase or propagation delay',
               'negative network predictions clamped only for audio, raw errors remain unclamped','small local training, not paper accuracy'])
    payload=json.dumps(metrics,indent=2);(out/'metrics.json').write_text(payload);(ROOT/'docs/neural-audio-metrics.json').write_text(payload)
    fig,axs=plt.subplots(2,3,figsize=(12,7),layout='constrained')
    for j in range(3):
        axs[0,j].plot(t,ref[j],lw=.6,label='BEM FFAT');axs[0,j].plot(t,pred[j],lw=.5,alpha=.7,label='AcousticNet');axs[0,j].legend()
        axs[0,j].set(xlabel='Time (s)',ylabel='Pressure (Pa)',title=f'Listener {j+1}')
        axs[1,j].imshow(np.r_[far[j].T,predictions[j].T],origin='lower');axs[1,j].set_title(f'Mode {j+1}: BEM below / network above')
    fig.savefig(out/'neural_audio.png',dpi=150);plt.close(fig)
    print(payload,flush=True)


if __name__=='__main__':main()
