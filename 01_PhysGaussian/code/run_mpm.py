"""Unmodified official MPM + Gaussian covariance update, small local scene.

Warp runs on CUDA; CPU torch is needed only because upstream modules import it.
The diagnostic orthographic Gaussian renderer is local, not the CUDA 3DGS renderer.
"""
import os
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):
    os.environ[key]='1'
os.environ['MPLBACKEND']='Agg'
import json
import time
import sys
import subprocess
from importlib.metadata import version
from pathlib import Path
import numpy as np
import warp as wp
from PIL import Image,ImageDraw
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT/'code'/'PhysGaussian'
sys.path.insert(0,str(REPO/'mpm_solver_warp'))
from mpm_solver_warp import MPM_Simulator_WARP
from mpm_utils import compute_cov_from_F
from warp_utils import set_mat33_to_identity
from warp_windows_compat import enable


def unpack(packed):
    cov=np.zeros((len(packed),3,3),dtype=np.float32)
    for j,(a,b) in enumerate(((0,0),(0,1),(0,2),(1,1),(1,2),(2,2))):
        cov[:,a,b]=packed[:,j];cov[:,b,a]=packed[:,j]
    return cov


def render(x,cov,colors,step,label,limits=(.20,.82,.25,.80),size=400,opacity=None):
    """Orthographic front-to-back alpha-composited anisotropic Gaussians."""
    xmin,xmax,zmin,zmax=limits
    scale=np.array([size/(xmax-xmin),-size/(zmax-zmin)])
    pix=(x[:,[0,2]]-np.array([xmin,zmax]))*scale
    projected=cov[:,[0,2]][:,:,[0,2]]*scale[None,:,None]*scale[None,None,:]
    projected+=np.eye(2)[None]*.3
    color=np.zeros((size,size,3),float)
    trans=np.ones((size,size),float)
    for i in np.argsort(x[:,1]):
        c=projected[i]
        r=int(np.ceil(3*np.sqrt(np.linalg.eigvalsh(c).max())))
        lo=np.maximum(np.floor(pix[i]-r).astype(int),0)
        hi=np.minimum(np.ceil(pix[i]+r).astype(int)+1,size)
        if np.any(hi<=lo):continue
        yy,xx=np.mgrid[lo[1]:hi[1],lo[0]:hi[0]]
        d=np.stack([xx-pix[i,0],yy-pix[i,1]],axis=-1)
        alpha=(.5 if opacity is None else opacity[i])*np.exp(-.5*np.einsum('...i,ij,...j->...',d,np.linalg.inv(c),d))
        sl=np.s_[lo[1]:hi[1],lo[0]:hi[0]]
        color[sl]+=trans[sl][...,None]*alpha[...,None]*colors[i]
        trans[sl]*=(1-alpha)
    img=Image.fromarray(np.uint8(np.clip(color+trans[...,None],0,1)*255))
    draw=ImageDraw.Draw(img)
    draw.text((10,10),f'{label} | t={step:.3f} s',fill=(20,25,30))
    draw.text((10,size-22),'Official MPM / local diagnostic Gaussian renderer',fill=(20,25,30))
    return img


def initialize(x,volume,cov,gravity,E=20000,device='cuda:0'):
    n=len(x)
    sim=MPM_Simulator_WARP(n,n_grid=32,grid_lim=1,device=device)
    sim.mpm_state.particle_x=wp.array(x,dtype=wp.vec3,device=device)
    sim.mpm_state.particle_vol=wp.array(volume,dtype=float,device=device)
    sim.mpm_state.particle_init_cov=wp.array(cov.reshape(-1),dtype=float,device=device)
    wp.launch(set_mat33_to_identity,dim=n,inputs=[sim.mpm_state.particle_F_trial],device=device)
    sim.set_parameters_dict({'E':float(E),'nu':.3,'material':'jelly','density':1000.,'g':gravity},device=device)
    sim.finalize_mu_lam(device=device)
    return sim


def state(sim,device):
    wp.launch(compute_cov_from_F,dim=sim.n_particles,inputs=[sim.mpm_state,sim.mpm_model],device=device)
    return (sim.mpm_state.particle_x.numpy(),sim.mpm_state.particle_F_trial.numpy(),
            unpack(sim.mpm_state.particle_cov.numpy().reshape(-1,6)))


def main():
    started=time.perf_counter();enable();wp.init()
    device='cuda:0'
    if not wp.is_cuda_available():raise RuntimeError('CUDA is unavailable for official GPU experiment')
    out=ROOT/'outputs'/'mpm_gaussians';out.mkdir(parents=True,exist_ok=True)
    h=.025
    points=np.stack(np.meshgrid(np.arange(12),np.arange(4),np.arange(4),indexing='ij'),axis=-1).reshape(-1,3)
    x=(points*h+np.array([.3125,.4625,.5625])).astype(np.float32)
    n=len(x);volume=np.full(n,h**3,dtype=np.float32)
    packed=np.zeros((n,6),np.float32);packed[:,[0,3,5]]=(h*.55)**2
    cov0=unpack(packed)
    dt=.0002

    # Free-fall control validates the official P2G/grid/G2P independently.
    sim=initialize(x,volume,packed,[0,0,-9.81],device=device)
    for s in range(100):sim.p2g2p(s,dt,device=device)
    free_x,free_F,free_cov=state(sim,device)
    expected=-9.81*dt*dt*100*101/2
    free_error=float(abs(np.mean(free_x[:,2]-x[:,2])-expected))
    assert free_error<2e-5,(free_error,expected)
    # Zero-gravity stress-free state is stationary.
    still=initialize(x,volume,packed,[0,0,0],device=device)
    for s in range(20):still.p2g2p(s,dt,device=device)
    still_x,_,_=state(still,device)
    stationary_error=float(np.max(np.abs(still_x-x)))
    assert stationary_error<1e-5,stationary_error

    all_metrics={};traces={}
    colors=np.c_[.15+.65*points[:,0]/11,.4+0*points[:,0],.7-.4*points[:,0]/11]
    for name,E in [('soft',20000),('stiff',80000)]:
        sim=initialize(x,volume,packed,[0,0,-9.81],E=E,device=device)
        sim.set_velocity_on_cuboid((.30,.5,.6),wp.vec3(.045,.15,.15),(0,0,0))
        frames=[];xs=[];Fs=[];covs=[];times=[];err=[];minimum=[];tip=[]
        count=2000
        for s in range(count+1):
            if s%25==0:
                xx,F,cov=state(sim,device)
                independent=F@cov0@F.transpose(0,2,1)
                e=float(np.max(np.abs(independent-cov))/np.max(np.abs(independent)))
                mineig=float(np.linalg.eigvalsh(cov).min())
                assert np.isfinite(xx).all() and np.isfinite(F).all() and mineig>0
                assert e<2e-5,e
                assert np.linalg.det(F).min()>.05
                xs.append(xx);Fs.append(F);covs.append(cov);times.append(s*dt);err.append(e);minimum.append(mineig)
                tip.append(float(np.mean(xx[points[:,0]>=10,2])))
                frames.append(render(xx,cov,colors,s*dt,f'E={E/1000:g} kPa'))
            if s<count:sim.p2g2p(s,dt,device=device)
        mass=float(sim.mpm_state.particle_mass.numpy().sum())
        assert np.isclose(mass,1000*volume.sum(),rtol=1e-6)
        frames[0].save(out/f'{name}.gif',save_all=True,append_images=frames[1:],duration=50,loop=0)
        frames[-1].save(out/f'{name}_final.png')
        np.savez_compressed(out/f'{name}_states.npz',time_s=times,positions_m=xs,deformation_gradient=Fs,
                            covariance_m2=covs,initial_positions_m=x,particle_volume_m3=volume,tip_mean_z_m=tip)
        all_metrics[name]=dict(E_Pa=E,total_mass_kg=mass,max_covariance_relative_error=max(err),
             min_covariance_eigenvalue_m2=min(minimum),maximum_tip_downward_displacement_m=float(tip[0]-min(tip)),
             final_tip_downward_displacement_m=float(tip[0]-tip[-1]),steps=count,dt_s=dt,frames=len(frames))
        traces[name]=(times,np.array(tip)-tip[0])
        print(name,all_metrics[name],flush=True)
    assert all_metrics['soft']['maximum_tip_downward_displacement_m']>all_metrics['stiff']['maximum_tip_downward_displacement_m']
    fig,ax=plt.subplots(figsize=(8,4.6),layout='constrained')
    for name,(tt,zz) in traces.items():ax.plot(tt,zz,label=f"{name}: E={all_metrics[name]['E_Pa']/1000:g} kPa")
    ax.set(xlabel='Time (s)',ylabel='Mean tip vertical displacement (m)',title='Official MPM cantilever: gravity, two elastic moduli')
    ax.legend();ax.grid(alpha=.2);fig.savefig(out/'tip_displacement.png',dpi=170);plt.close(fig)
    commit=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()
    metrics=dict(scope='official CUDA MPM + official Gaussian covariance kernel on local synthetic beam; diagnostic renderer only',
                 all_checks_passed=True,commit=commit,device=str(wp.get_device(device)),warp_version=version('warp-lang'),
                 particles=n,grid=[32]*3,free_fall_mean_position_error_m=free_error,stationary_position_error_m=stationary_error,
                 cases=all_metrics,elapsed_s=time.perf_counter()-started)
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    (ROOT/'docs'/'RESULTS.md').write_text(f'''# PhysGaussian 官方物理模块复现结果

运行上游提交 `{commit}` 未修改的 MPM_Simulator_WARP 和 compute_cov_from_F，在 RTX 2050 上推进 {n} 个材料点 / 高斯。网格 32³，dt=0.0002 s，两组弹性模量分别 20 kPa / 80 kPa，各 2000 步。

## 验证

- 无边界自由落体平均位置误差：{free_error:.3e} m；按半隐式 Euler 的离散解析解比较。
- 零重力静止态最大位置误差：{stationary_error:.3e} m。
- Σ=FΣ₀Fᵀ：独立 NumPy 与官方 Warp 核最大相对差 {max(c['max_covariance_relative_error'] for c in all_metrics.values()):.3e}。
- 两组所有输出时刻协方差正定、变形梯度有限且未翻转；粒子总质量恒定。
- 软/硬梁最大端部下挠：{all_metrics['soft']['maximum_tip_downward_displacement_m']:.6f} / {all_metrics['stiff']['maximum_tip_downward_displacement_m']:.6f} m。

## 文件

`outputs/mpm_gaussians/soft.gif`、`stiff.gif` 为可播放动画；`tip_displacement.png` 为力学对照；`*_states.npz` 为每帧位置、F、Σ、体积与时间。

## 复现层次

这是官方物理求解与高斯运动学模块复现，输入为本地合成梁，不是论文照片重建场景。渲染为本地正交投影的各向异性高斯 alpha 合成，仅用于诊断，没有训练外观、SH、透视相机、原 CUDA 光栅器或论文画质指标。图像不能冒充原官方端到端渲染结果。
PyTorch 使用 CPU 包以满足官方导入；实际物理计算由 Warp CUDA 执行。核调用和输入适配在上游仓库外，未改作者源文件。
''',encoding='utf-8')
    print(json.dumps(metrics,indent=2))


if __name__=='__main__':main()
