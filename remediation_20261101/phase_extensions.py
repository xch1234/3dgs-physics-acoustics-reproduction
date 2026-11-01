"""Phase-preserving variants of static 12-mode and moving-listener playback."""
import sys,json
from common import ROOT,AUDIT,save
import numpy as np
from scipy.signal import hilbert
from scipy.io import wavfile
sys.path.insert(0,str(ROOT/'02_PAT/code'))
import run_pat_extended as ext
from phase_audio import synthesize_phase_preserving
source=AUDIT/'pat_extensions/outputs/pat_extended';out=AUDIT/'pat_extensions/outputs/phase_preserving';out.mkdir(parents=True,exist_ok=True)
data=dict(np.load(ROOT/'verification_20261101/fresh_cpu_pipeline_retry/fem/official_fem_result.npz'))
mesh_data=np.load(source/'beam_mesh.npz');mesh=ext.geometry(mesh_data['vertices'],mesh_data['triangles'])
freq=data['frequencies_Hz'];omega=2*np.pi*freq;decay=(30+1e-6*omega**2)/2;wd=np.sqrt(omega**2-decay**2);k=omega/343
full=np.zeros((len(data['vertices_m'])*3,12));full[data['free_dofs']]=data['clamped_modes_mass_normalized'];hit=int(np.argmax(data['vertices_m']@np.array([1,.1,.01])))
impulse=full.reshape(-1,3,12)[hit,1]*.001;fs=48000;t=np.arange(fs*3)/fs
def q_at(events):
 q=np.zeros((12,len(t)))
 for event in events:
  age=np.maximum(t-event,0);q+=impulse[:,None]/wd[:,None]*np.exp(-decay[:,None]*age)*np.sin(wd[:,None]*age)*(t>=event)
 return q
def transfers(points):
 bem=[];pat=[]
 for j in range(12):
  m=np.load(source/f'mode_{j+1:02d}.npz');bem.append(ext.pressure(points,mesh,k[j],m['density']));pat.append(ext.evaluate(points,m['centers'],m['coefficients'],k[j]))
 return np.array(bem).T,np.array(pat).T
q=q_at([0]);H,P=transfers(np.eye(3)*.3);b=synthesize_phase_preserving(H,q);p=synthesize_phase_preserving(P,q)
moving=np.load(AUDIT/'pat_extensions/outputs/moving_listener/raw.npz');control=moving['control_time_s'];Hm=moving['bem_transfer'];Pm=moving['pat_transfer'];qm=q_at(np.arange(0,3,.5));z=hilbert(qm,axis=1)
def moving_audio(transfer,state):
 h=np.array([np.interp(t,control,transfer[:,j].real)+1j*np.interp(t,control,transfer[:,j].imag) for j in range(12)])
 return np.real((h*state).sum(axis=0))
bm=moving_audio(Hm,z);pm=moving_audio(Pm,z)
T=np.eye(12);ang=.67;T[:2,:2]=[[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]];T[2,2]=-1
static_error=float(np.linalg.norm(synthesize_phase_preserving(H@T,T.T@q)-b)/np.linalg.norm(b))
moving_error=float(np.linalg.norm(moving_audio(Hm@T,T.T@z)-bm)/np.linalg.norm(bm));assert max(static_error,moving_error)<1e-12
signals={**{f'{name}_{axis}':v[j] for name,v in [('bem_static',b),('pat_static',p)] for j,axis in enumerate('xyz')},'bem_moving':bm,'pat_moving':pm}
gain=.85/max(np.abs(v).max() for v in signals.values());fade=np.ones(len(t));fade[-960:]=np.linspace(1,0,960)
for name,sig in signals.items():
 pcm=np.rint(sig*gain*fade*32767).astype(np.int16);wavfile.write(out/(name+'.wav'),fs,pcm);sr,back=wavfile.read(out/(name+'.wav'));assert sr==fs and np.array_equal(back,pcm)
np.savez_compressed(out/'raw.npz',time_s=t,static_q=q,moving_q=qm,static_bem_pressure=b,static_pat_pressure=p,moving_bem_pressure=bm,moving_pat_pressure=pm,common_gain=gain,static_bem_transfer=H,static_pat_transfer=P)
r=dict(passed=True,static_basis_relative_error=static_error,moving_basis_relative_error=moving_error,static_PAT_BEM_audio_relative_L2=float(np.linalg.norm(p-b)/np.linalg.norm(b)),moving_PAT_BEM_audio_relative_L2=float(np.linalg.norm(pm-bm)/np.linalg.norm(bm)),waves=len(signals),sample_rate_hz=fs,scope='Local complex narrowband extension to historical 12-mode and moving-listener magnitude playback; not original PAT output, retarded acoustics or Doppler.')
save('checks/V08-extensions.json',r);print(json.dumps(r,indent=2))
