import os,sys,json,shutil
from pathlib import Path
from common import ROOT,AUDIT,save
test_tag='_clean_env' if 'physgaussian-clean' in sys.prefix else ''
# Compile new Warp source in an ASCII Linux directory; original source stays untouched.
code=Path('/opt/3dgs-runtime/remediation-code');code.mkdir(exist_ok=True)
shutil.copy2(ROOT/'01_PhysGaussian/code/snow_adapter.py',code/'snow_adapter.py')
sys.path[:0]=[str(code),'/opt/3dgs-runtime/PhysGaussian-source/mpm_solver_warp',str(ROOT/'01_PhysGaussian/code')]
import mpm_solver_warp as solver
import validate_materials as base
import snow_adapter as adapter
import numpy as np
import warp as wp
wp.init();wp.config.kernel_cache_dir='/opt/3dgs-runtime/remediation-warp-cache'
def make():
 s=base.make('snow');adapter.initialize_plastic_volume(s);return s
mu=20000/(2*1.3);lam=20000*.3/(1.3*.4)
def reference(F,jp):
 U,s,Vt=np.linalg.svd(F);clipped=np.clip(s,.975,1.0075);Fe=U@np.diag(clipped)@Vt
 j=np.clip(jp*np.linalg.det(F)/np.linalg.det(Fe),.6,20);h=np.exp(10*(1-j));J=np.linalg.det(Fe)
 stress=h*(2*mu*(Fe-U@Vt)@Fe.T+np.eye(3)*lam*J*(J-1))
 return stress,Fe,j
errors=[];rng=np.random.default_rng(20261101)
with adapter.install(solver):
 for i in range(30):
  Q,_=np.linalg.qr(rng.normal(size=(3,3)));Q[:,0]*=np.linalg.det(Q);F=Q@np.diag(rng.uniform(.9,1.1,3))
  sim=make();tau,Fe=base.stress(sim,F);expected,ef,jp=reference(F,1)
  err=np.linalg.norm(tau-expected)/max(np.linalg.norm(expected),1);errors.append(float(err));assert err<2e-4
  assert np.allclose(Fe,ef,rtol=2e-5,atol=2e-6);assert abs(sim.mpm_state.particle_Jp.numpy()[0]-jp)<1e-5
 rigid,_=base.stress(make(),Q);assert np.linalg.norm(rigid)<.2
 F=np.eye(3);F[0,1]=.005;sim=make();elastic,_=base.stress(sim,F);assert np.linalg.norm(elastic)>1
 sim=make();previous=np.eye(3);Fe=np.eye(3);gamma=np.r_[np.linspace(0,.3,101),np.linspace(.3,0,101)[1:]];values=[];jp=[]
 for g in gamma:
  total=np.eye(3);total[0,1]=g;trial=total@np.linalg.inv(previous)@Fe;tau,Fe=base.stress(sim,trial);previous=total
  values.append(tau);jp.append(float(sim.mpm_state.particle_Jp.numpy()[0]))
 assert np.isfinite(values).all() and np.max(np.abs(np.array(values)[:,0,1]))>1
 out=AUDIT/('snow'+test_tag);out.mkdir(exist_ok=True);np.savez_compressed(out/'load_unload.npz',gamma=gamma,stress=values,Jp=jp)
 # Spatial check: actual upstream grid transfer/MPM steps with new material dispatch.
 xyz=np.array([[x,y,z] for x in np.linspace(.4,.6,5) for y in np.linspace(.4,.6,5) for z in np.linspace(.45,.65,5)],np.float32)
 cov=np.tile([.0001,0,0,.0001,0,.0001],(len(xyz),1));vol=np.full(len(xyz),.05**3,np.float32)
 sim=base.initialize(xyz,vol,cov,[0,0,-9.8]);sim.set_parameters_dict({'material':'snow'},device='cuda:0');adapter.initialize_plastic_volume(sim)
 sim.add_surface_collider((0,0,.25),(0,0,1),surface='sticky')
 initial_mass=float(sim.mpm_state.particle_mass.numpy().sum())
 trajectory=[]
 for i in range(4000):
  sim.p2g2p(i,.0001,device='cuda:0')
  if (i+1)%100==0:trajectory.append(sim.mpm_state.particle_x.numpy())
 x=sim.mpm_state.particle_x.numpy();assert np.isfinite(x).all();assert abs(sim.mpm_state.particle_mass.numpy().sum()-initial_mass)<1e-6
 assert x[:,2].min()>.20, 'Particles penetrated far below collider'
 assert np.max(np.abs(sim.mpm_state.particle_F.numpy()-np.eye(3)))>.001, 'Expected deformation after floor contact'
 np.savez_compressed(out/'spatial_final.npz',initial=xyz,final=x,F=sim.mpm_state.particle_F.numpy(),Jp=sim.mpm_state.particle_Jp.numpy(),time_s=np.arange(1,41)*.01,trajectory=trajectory)
r={'passed':True,'scope':'local snow extension, not upstream snow reproduction or experimental material validation','max_numpy_stress_relative_error':max(errors),'rigid_stress_norm':float(np.linalg.norm(rigid)),'max_shear':float(np.max(np.abs(np.array(values)[:,0,1]))),'spatial_steps':4000,'particles':len(xyz),'mass_preserved':True,'min_height':float(x[:,2].min())}
save('checks/V19-snow-extension'+test_tag+'.json',r);print(json.dumps(r,indent=2))
# Replace this process so its CUDA allocations are released before full rendering.
os.execv(sys.executable,[sys.executable,'-u',str(AUDIT/'test_snow_scene.py')])
