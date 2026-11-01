"""Re-run local PAT in a separate folder, retaining original magnitude output."""
import sys,json
from pathlib import Path
import numpy as np
from scipy.io import wavfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'02_PAT/code'))
from phase_audio import synthesize_phase_preserving
import run_pat
A=ROOT/'remediation_20261101';out=A/'pat_phase';(out/'docs').mkdir(parents=True,exist_ok=True)
run_pat.ROOT=out;run_pat.OUT=out/'outputs/pat_pipeline';run_pat.FEM=ROOT/'verification_20261101/fresh_cpu_pipeline_retry/fem/official_fem_result.npz'
run_pat.main()
raw=dict(np.load(run_pat.OUT/'pressure_audio_raw.npz'));q=raw['modal_response'];H=raw['transfer_bem']
rng=np.random.default_rng(20261101);sign=np.diag(rng.choice([-1,1],q.shape[0]));rotation=np.eye(q.shape[0]);angle=.73;rotation[:2,:2]=[[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]]
p=synthesize_phase_preserving(H,q);errors={}
for name,T in [('sign_flip',sign),('degenerate_pair_rotation',rotation)]:
 transformed=synthesize_phase_preserving(H@T,T.T@q);errors[name]=float(np.linalg.norm(transformed-p)/np.linalg.norm(p));assert errors[name]<1e-12
old=np.load(ROOT/'verification_20261101/pat/outputs/pat_pipeline/pressure_audio_raw.npz')
new=np.load(ROOT/'verification_20261101/fresh_cpu_pipeline_retry/pat/outputs/pat_pipeline/pressure_audio_raw.npz')
a=synthesize_phase_preserving(old['transfer_bem'],old['modal_response']);b=synthesize_phase_preserving(new['transfer_bem'],new['modal_response'])
errors['independent_FEM_eigensolver_bases']=float(np.linalg.norm(a-b)/np.linalg.norm(a));assert errors['independent_FEM_eigensolver_bases']<1e-8
pat=synthesize_phase_preserving(raw['transfer_pat'],q);gain=.85/max(abs(p).max(),abs(pat).max());fade=np.ones(q.shape[1]);fade[-960:]=np.linspace(1,0,960)
folder=out/'outputs/phase_preserving';folder.mkdir(parents=True,exist_ok=True)
for tag,signals in [('bem',p),('pat',pat)]:
 for idx,axis in enumerate('xyz'):
  pcm=np.rint(signals[idx]*gain*fade*32767).astype(np.int16);wavfile.write(folder/f'{tag}_{axis}.wav',48000,pcm)
  sr,back=wavfile.read(folder/f'{tag}_{axis}.wav');assert sr==48000 and np.array_equal(pcm,back)
np.savez_compressed(folder/'raw.npz',pressure_bem=p,pressure_pat=pat,modal_response=q,transfer_bem=H,transfer_pat=raw['transfer_pat'],common_gain=gain)
r={'passed':True,'basis_invariance_relative_errors':errors,'PAT_vs_BEM_audio_relative_L2':float(np.linalg.norm(pat-p)/np.linalg.norm(p)),'scope':'Local phase-preserving extension; original magnitude-only path retained as historical paper-style baseline; not full transient acoustics or proof of paper correctness','method':'real(H @ hilbert(q)), exp(+i omega t), transfer sampled at modal frequencies; finite-window Hilbert edge effects, no propagation-delay/contact solver'}
(A/'checks/V08.json').write_text(json.dumps(r,indent=2),encoding='utf8');print(json.dumps(r,indent=2))
