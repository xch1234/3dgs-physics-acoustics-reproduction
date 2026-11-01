"""Bind the actual learned hybrid/AcousticNet sound sample to Gaussian motion.

Trilinear FEM interpolation drives centers and F Sigma F^T. Gaussians are
procedural voxel representatives, not a photometrically trained 3DGS. No MPM.
The original magnitude-FFAT audio limitation and prediction errors are retained.
"""
import sys,json,itertools,shutil,subprocess
from pathlib import Path
from common import ROOT,AUDIT,save,digest
import numpy as np
from scipy.spatial import cKDTree
from scipy.io import wavfile
import torch
from PIL import Image,ImageDraw
sys.path.insert(0,str(ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting'))
from diff_gaussian_rasterization import GaussianRasterizationSettings,GaussianRasterizer
from utils.graphics_utils import getProjectionMatrix
torch.set_num_threads(2);torch.set_grad_enabled(False)
source=AUDIT/'neural_extensions/outputs/neural_audio';d=dict(np.load(source/'raw.npz'));out=AUDIT/'unified_neural_box';out.mkdir(exist_ok=True)
vertices=d['vertices_m'];voxel=d['voxel'];cells=np.argwhere(voxel);h=.15/voxel.shape[0]
origin=vertices.min(0)-cells.min(0)*h;corners=np.array(list(itertools.product([0,1],repeat=3)))
positions=(cells[:,None]+corners[None])*h+origin
distance,indices=cKDTree(vertices).query(positions.reshape(-1,3));assert distance.max()<1e-9
indices=indices.reshape(-1,8);node_modes=d['modes_mass_normalized'].reshape(-1,3,6);values=node_modes[indices]
center=(cells+.5)*h+origin;center_modes=values.mean(1);gradient=np.einsum('nvcm,va->ncam',values,(2*corners-1)/(4*h))
freq=d['frequencies_Hz'];omega=2*np.pi*freq;decay=.5*(float(d['rayleigh_alpha'])+float(d['rayleigh_beta'])*omega**2);wd=np.sqrt(omega**2-decay**2);J=d['modal_impulse']
# A conservative strain bound prevents an exaggerated display from inverting cells.
strain_bound=float(np.max(np.sqrt(np.sum(gradient**2,axis=(1,2)))@(np.abs(J)/wd)))
display_gain=min(200.,.35/max(strain_bound,1e-30))
def trajectory(t):
 t=np.atleast_1d(t);return J[:,None]/wd[:,None]*np.exp(-decay[:,None]*t)*np.sin(wd[:,None]*t)
q=trajectory(d['time_s']);np.testing.assert_allclose(q,d['modal_q'],rtol=1e-12,atol=1e-15)
listener_indices=[(0,15),(16,15),(32,8)];ref=np.array([d['bem_ffat'][:,a,b]*omega**2/.3 for a,b in listener_indices])@q
pred=np.array([np.maximum(d['neural_ffat'],0)[:,a,b]*omega**2/.3 for a,b in listener_indices])@q
np.testing.assert_allclose(ref,d['bem_pressure_Pa'],rtol=1e-10,atol=1e-12);np.testing.assert_allclose(pred,d['neural_pressure_Pa'],rtol=1e-10,atol=1e-12)
# Independent affine test: interpolation reproduces any affine displacement,
# and its gradient matches the prescribed constant matrix.
B=np.array([[.01,.02,0],[-.03,.01,.04],[0,.02,-.01]]);c=np.array([.1,.2,.3]);uv=positions@B.T+c
np.testing.assert_allclose(uv.mean(1),center@B.T+c,atol=1e-14)
np.testing.assert_allclose(np.einsum('nvc,va->nca',uv,(2*corners-1)/(4*h)),np.broadcast_to(B,(len(cells),3,3)),atol=1e-12)
target=(vertices.min(0)+vertices.max(0))/2;extent=np.ptp(vertices,axis=0).max();eye=target+extent*np.array([2.2,2.3,1.6]);forward=target-eye;forward/=np.linalg.norm(forward);right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);down=np.cross(forward,right)
R=np.array([right,down,forward]);view=np.eye(4);view[:3,:3]=R;view[:3,3]=-R@eye;view=torch.tensor(view,dtype=torch.float32,device='cuda').T.contiguous()
fy=.57;fx=2*np.arctan(np.tan(fy/2)*640/360);projection=getProjectionMatrix(.001,10.,fx,fy).T.cuda()
settings=GaussianRasterizationSettings(image_height=360,image_width=640,tanfovx=float(np.tan(fx/2)),tanfovy=float(np.tan(fy/2)),bg=torch.ones(3,device='cuda'),scale_modifier=1.,viewmatrix=view,projmatrix=view@projection,sh_degree=0,campos=torch.tensor(eye,dtype=torch.float32,device='cuda'),prefiltered=False,debug=False)
raster=GaussianRasterizer(raster_settings=settings);u=(center[:,0]-center[:,0].min())/max(np.ptp(center[:,0]),h)
colors=torch.tensor(np.c_[.2+.6*u,np.full(len(center),.5),.8-.5*u],dtype=torch.float32,device='cuda');opacity=torch.full((len(center),1),.85,device='cuda');cov0=np.eye(3)[None]*(h*.55)**2
min_det=1.;min_eig=float('inf');max_displacement=0.
def render(t,scale):
 global min_det,min_eig,max_displacement
 qt=trajectory(t)[:,0];displacement=np.einsum('ncm,m->nc',center_modes,qt);F=np.eye(3)[None]+scale*np.einsum('ncam,m->nca',gradient,qt);cov=F@cov0@F.transpose(0,2,1)
 min_det=min(min_det,float(np.linalg.det(F).min()));min_eig=min(min_eig,float(np.linalg.eigvalsh(cov).min()));max_displacement=max(max_displacement,float(np.linalg.norm(displacement,axis=1).max()));assert min_det>0 and min_eig>0
 xyz=torch.tensor(center+scale*displacement,dtype=torch.float32,device='cuda');packed=cov[:,[0,0,0,1,1,2],[0,1,2,1,2,2]]
 im,radius=raster(means3D=xyz,means2D=torch.zeros_like(xyz),colors_precomp=colors,opacities=opacity,cov3D_precomp=torch.tensor(packed,dtype=torch.float32,device='cuda'));assert int((radius>0).sum())>.9*len(center)
 rgb=(im.clamp(0,1).permute(1,2,0).cpu().numpy()*255).round().astype(np.uint8);assert np.mean(rgb<240)>.01;return Image.fromarray(rgb)
frames=out/'frames';frames.mkdir(exist_ok=True)
for i,t in enumerate(np.arange(90)/30):
 a=render(t,1.);b=render(t,display_gain);im=Image.new('RGB',(1280,400),'white');im.paste(a,(0,35));im.paste(b,(640,35));draw=ImageDraw.Draw(im)
 draw.text((10,8),f'Same held-out box_21 / learned hybrid modes | time {t:.3f}s | true scale (left) / displacement x{display_gain:.2f} (right)',fill='black')
 draw.text((10,385),'Procedural Gaussian voxels / CUDA splatting / trilinear FEM transport | no photometric training or MPM/contact',fill='black');im.save(frames/f'{i:04d}.png')
slow=out/'slow_frames';slow.mkdir(exist_ok=True)
for i,t in enumerate(np.arange(120)/(30*1000)):
 im=render(t,display_gain);draw=ImageDraw.Draw(im);draw.rectangle((0,0,640,38),fill='white');draw.text((8,5),f'Time slowed 1000x / displacement x{display_gain:.2f} / physical time {t*1000:.3f} ms',fill='black');draw.text((8,21),'Silent diagnostic; learned modes with numerical refinement',fill='black');im.save(slow/f'{i:04d}.png')
commands=[];ffmpeg='/opt/3dgs-runtime/envs/physgaussian/bin/ffmpeg'
for name in ('bem','neural'):
 wav=out/(name+'.wav');shutil.copy2(source/(name+'_listener_1.wav'),wav);sr,pcm=wavfile.read(wav);assert sr==48000 and len(pcm)==144000
 cmd=[ffmpeg,'-y','-framerate','30','-i',str(frames/'%04d.png'),'-i',str(wav),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(out/(name+'_synchronized.mp4'))];subprocess.run(cmd,check=True);commands.append(cmd)
cmd=[ffmpeg,'-y','-framerate','30','-i',str(slow/'%04d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(out/'slow_motion_silent.mp4')];subprocess.run(cmd,check=True);commands.append(cmd)
np.savez_compressed(out/'binding.npz',gaussian_centers_m=center,gaussian_modes=center_modes,modal_gradients=gradient,corner_vertex_indices=indices,voxel_size_m=h)
metrics=dict(executed=True,scope='Actual current learned hybrid modes and AcousticNet output for the SAME held-out box drive Gaussian rendering and audio. Trilinear center/F transport; procedural Gaussians, no photos/MPM/contact. FFAT remains magnitude-only.',source_sha256=digest(source/'raw.npz'),gaussians=len(center),shared_modal_trajectory_verified=True,audio_recomputation_verified=True,affine_interpolation_test_passed=True,min_visual_F_determinant=min_det,min_visual_covariance_eigenvalue=min_eig,physical_max_sampled_displacement_m=max_displacement,per_listener_neural_BEM_audio_relative_L2=(np.linalg.norm(pred-ref,axis=1)/np.linalg.norm(ref,axis=1)).tolist(),frame_count=90,seconds=3.,fps=30,visual_displacement_gain=display_gain,visual_gain_policy='at most 200, conservatively bounded to amplified gradient norm <=0.35',slow_motion_time_factor=1000,ffmpeg_commands=commands,limits=['Published FFAT magnitude convention; no phase/propagation delay or basis invariance claim','Learned-network errors retained, not corrected by rendering','Only procedural voxel Gaussian representation; not photometrically reconstructed 3DGS','No MPM-contact to high-frequency modal coupling; 30 fps cannot resolve true acoustic vibration'])
save('checks/V31-neural-box-prototype.json',metrics);(out/'metrics.json').write_text(json.dumps(metrics,indent=2));print(json.dumps(metrics,indent=2))
