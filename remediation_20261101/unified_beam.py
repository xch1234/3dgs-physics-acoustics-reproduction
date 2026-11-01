"""Same-object modal/Gaussian/acoustic prototype, not a learned 3DGS or MPM system.

One clamped FEM beam, one 0.001 N s impulse, and one modal trajectory drive
surface Gaussians and complex PAT/BEM audio. Uses the original CUDA rasterizer.
The procedural Gaussians are not a photometrically reconstructed scene.
"""
import sys,json,math,subprocess
from pathlib import Path
from common import ROOT,AUDIT,save,digest
import numpy as np
import torch
from PIL import Image,ImageDraw
from scipy.io import wavfile
sys.path.insert(0,str(ROOT/'02_PAT/code'))
import run_pat as pat
from phase_audio import synthesize_phase_preserving
sys.path.insert(0,str(ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting'))
from diff_gaussian_rasterization import GaussianRasterizationSettings,GaussianRasterizer
from utils.graphics_utils import getProjectionMatrix
torch.set_grad_enabled(False);torch.set_num_threads(2)
out=AUDIT/'unified_beam';out.mkdir(exist_ok=True)
fem_path=ROOT/'verification_20261101/fresh_cpu_pipeline_retry/fem/official_fem_result.npz'
data=dict(np.load(fem_path));raw=dict(np.load(AUDIT/'pat_phase/outputs/phase_preserving/raw.npz'))
vertices,faces,modes=pat.beam_surface(data)
# Linear surface interpolation is shared by rest geometry and all modal fields.
for _ in range(2):vertices,faces,modes=pat.refine(vertices,faces,modes)
modes=modes[:,:,:6];tri=vertices[faces];tri_modes=modes[faces]
rest=tri.mean(1);rest_mode=tri_modes.mean(1)
edge1=tri[:,1]-tri[:,0];edge2=tri[:,2]-tri[:,0]
normal=np.cross(edge1,edge2);area=np.linalg.norm(normal,axis=1)/2;normal/=np.linalg.norm(normal,axis=1)[:,None]
rest_basis=np.stack([edge1,edge2,normal],axis=2);inv_basis=np.linalg.inv(rest_basis)
cov0=np.eye(3)[None]*area[:,None,None]*.5
full=np.zeros((len(data['vertices_m'])*3,6));full[data['free_dofs']]=data['clamped_modes_mass_normalized'][:,:6]
omega=2*np.pi*data['frequencies_Hz'][:6];decay=(30+1e-6*omega**2)/2;wd=np.sqrt(omega**2-decay**2)
hit=int(np.argmax(data['vertices_m']@np.array([1,.1,.01])))
J=full.reshape(-1,3,6)[hit,1]*.001
def trajectory(t):
 t=np.atleast_1d(t);q=J[:,None]/wd[:,None]*np.exp(-decay[:,None]*t)*np.sin(wd[:,None]*t)
 qdot=J[:,None]*np.exp(-decay[:,None]*t)*(np.cos(wd[:,None]*t)-decay[:,None]/wd[:,None]*np.sin(wd[:,None]*t))
 return q,qdot
fs=48000;t=np.arange(fs*3)/fs;q,qd=trajectory(t)
assert np.allclose(q,raw['modal_response'],rtol=1e-12,atol=1e-15)
M=data['M_kg'];mass_error=float(np.linalg.norm(full.T@M@full-np.eye(6)))
assert mass_error<1e-8
E=.5*np.sum(qd**2+omega[:,None]**2*q**2,axis=0)
assert np.all(np.diff(E)<=1e-12*max(E))
assert np.allclose(E[0],.5*np.dot(J,J))
assert np.max(np.abs(full[np.setdiff1d(np.arange(len(full)),data['free_dofs'])]))==0
bem=synthesize_phase_preserving(raw['transfer_bem'],q);approx=synthesize_phase_preserving(raw['transfer_pat'],q)
assert np.allclose(bem,raw['pressure_bem'],rtol=1e-12,atol=1e-12)
gain=.85/max(np.abs(bem).max(),np.abs(approx).max());fade=np.ones(len(t));fade[-960:]=np.linspace(1,0,960)
for name,p in [('bem',bem),('pat',approx)]:
 pcm=np.rint(p[0]*gain*fade*32767).astype(np.int16);wavfile.write(out/(name+'.wav'),fs,pcm)
 sr,check=wavfile.read(out/(name+'.wav'));assert sr==fs and np.array_equal(check,pcm)
if '--prepare-only' in sys.argv:
 save('checks/V31-preparation.json',dict(mass_orthogonality_error=mass_error,energy_nonincreasing=True,shared_modal_trajectory_matches_PAT=True,gaussians=len(rest),scope='CPU mathematical preparation only; CUDA render not yet checked'))
 print('Shared trajectory and acoustic preparation passed',flush=True);raise SystemExit(0)
eye=np.array([.23,.24,.16]);target=np.zeros(3);forward=(target-eye);forward/=np.linalg.norm(forward)
right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);down=np.cross(forward,right)
R=np.array([right,down,forward]);V=np.eye(4);V[:3,:3]=R;V[:3,3]=-R@eye
view=torch.tensor(V,dtype=torch.float32,device='cuda').T.contiguous()
fy=.57;fx=2*np.arctan(np.tan(fy/2)*640/360)
projection=getProjectionMatrix(.01,10.,fx,fy).T.cuda();fullproj=view@projection
settings=GaussianRasterizationSettings(image_height=360,image_width=640,tanfovx=float(np.tan(fx/2)),tanfovy=float(np.tan(fy/2)),bg=torch.ones(3,device='cuda'),scale_modifier=1.,viewmatrix=view,projmatrix=fullproj,sh_degree=0,campos=torch.tensor(eye,dtype=torch.float32,device='cuda'),prefiltered=False,debug=False)
raster=GaussianRasterizer(raster_settings=settings)
colors=np.c_[.2+.6*(rest[:,0]+.06)/.12,np.full(len(rest),.45),.85-.5*(rest[:,0]+.06)/.12]
color=torch.tensor(colors,dtype=torch.float32,device='cuda');opacity=torch.full((len(rest),1),.85,device='cuda')
min_eig=float('inf');max_displacement=0.;counts=[]
def render(time,amplification):
 global min_eig,max_displacement
 qt=trajectory(time)[0][:,0];displacement=np.einsum('ncm,m->nc',rest_mode,qt)
 max_displacement=max(max_displacement,float(np.linalg.norm(displacement,axis=1).max()))
 moved=tri+amplification*np.einsum('nvcm,m->nvc',tri_modes,qt)
 e1=moved[:,1]-moved[:,0];e2=moved[:,2]-moved[:,0];n=np.cross(e1,e2);n/=np.linalg.norm(n,axis=1)[:,None]
 F=np.stack([e1,e2,n],axis=2)@inv_basis;cov=F@cov0@F.transpose(0,2,1)
 min_eig=min(min_eig,float(np.linalg.eigvalsh(cov).min()));assert min_eig>0
 packed=cov[:,[0,0,0,1,1,2],[0,1,2,1,2,2]]
 xyz=torch.tensor(rest+amplification*displacement,dtype=torch.float32,device='cuda')
 image,radii=raster(means3D=xyz,means2D=torch.zeros_like(xyz),colors_precomp=color,opacities=opacity,cov3D_precomp=torch.tensor(packed,dtype=torch.float32,device='cuda'))
 counts.append(int((radii>0).sum()));assert counts[-1]>.9*len(rest)
 pixels=(image.clamp(0,1).permute(1,2,0).cpu().numpy()*255).round().astype(np.uint8)
 assert np.mean(pixels<240)>.01
 return Image.fromarray(pixels)
frames=out/'frames';frames.mkdir(exist_ok=True)
for i,tm in enumerate(np.arange(90)/30):
 a=render(tm,1.);b=render(tm,50.);canvas=Image.new('RGB',(1280,400),'white');canvas.paste(a,(0,35));canvas.paste(b,(640,35));draw=ImageDraw.Draw(canvas)
 draw.text((15,8),f'SAME FEM BEAM | real time {tm:.3f} s | left: true scale | right: displacement x50',fill='black')
 draw.text((15,385),'Procedural Gaussians / original CUDA renderer | 30 fps cannot resolve kHz vibration | no MPM/contact',fill='black')
 canvas.save(frames/f'{i:04d}.png')
slow=out/'slow_frames';slow.mkdir(exist_ok=True)
for i,tm in enumerate(np.arange(120)/(30*500)):
 im=render(tm,50.);draw=ImageDraw.Draw(im);draw.rectangle((0,0,640,38),fill='white')
 draw.text((8,5),f'Time slowed 500x | displacement x50 | physical t={tm*1000:.3f} ms',fill='black')
 draw.text((8,20),'Silent diagnostic / NOT physical-speed motion',fill='black');im.save(slow/f'{i:04d}.png')
ffmpeg='/opt/3dgs-runtime/envs/physgaussian/bin/ffmpeg'
cmds=[]
for name in ('bem','pat'):
 cmd=[ffmpeg,'-y','-framerate','30','-i',str(frames/'%04d.png'),'-i',str(out/(name+'.wav')),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(out/(name+'_synchronized.mp4'))];subprocess.run(cmd,check=True);cmds.append(cmd)
cmd=[ffmpeg,'-y','-framerate','30','-i',str(slow/'%04d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(out/'slow_motion_silent.mp4')];subprocess.run(cmd,check=True);cmds.append(cmd)
np.savez_compressed(out/'shared_state.npz',time_s=t,modal_q=q,modal_qdot=qd,modal_energy_J=E,rest_gaussians_m=rest,gaussian_modes=rest_mode,rest_covariance=cov0,frequencies_Hz=omega/(2*np.pi),modal_impulse=J,pressure_bem_Pa=bem,pressure_pat_Pa=approx,common_audio_gain=gain)
r=dict(executed=True,scope='Local same-object FEM -> Gaussian surface motion + phase-preserving PAT/BEM audio prototype. Procedural Gaussians, not a trained 3DGS; no MPM/contact or learned NeuralSound inference.',gaussians=len(rest),modes=6,impulse_Ns=.001,hit_vertex=hit,mass_orthogonality_error=mass_error,energy_nonincreasing=True,initial_retained_modal_energy_J=float(E[0]),physical_max_sampled_displacement_m=max_displacement,min_covariance_eigenvalue_m2=min_eig,minimum_visible_gaussians=min(counts),PAT_BEM_audio_relative_L2=float(np.linalg.norm(approx-bem)/np.linalg.norm(bem)),audio_rate_hz=fs,video_rate_hz=30,duration_s=3.,real_time_frames=90,diagnostic_displacement_gain=50,slow_motion_time_factor=500,ffmpeg_commands=cmds,fem_sha256=digest(fem_path),limitations=['Finite-band modal acoustics, no propagation delay; finite Hilbert window edge effects','Surface interpolation with normal extension for covariance transport, not full volumetric MPM','Synthesized surface Gaussians have no photometric training; no general learned-object binding','30 fps video undersamples real acoustic vibration; silent 500x slow motion is diagnostic only'])
save('checks/V31-local-prototype.json',r);(out/'metrics.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
