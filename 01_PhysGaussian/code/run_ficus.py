"""All retained official Ficus Gaussians in the official MPM solver.

Shortened official dynamics, NumPy preprocessing replacing CUDA/Taichi helpers,
and a sampled diagnostic orthographic renderer; not the original render pipeline.
"""
import os
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):
    os.environ[key]='1'
import json
import time
import hashlib
import subprocess
from pathlib import Path
import numpy as np
import warp as wp
from run_mpm import ROOT,REPO,MPM_Simulator_WARP,set_mat33_to_identity,compute_cov_from_F,unpack,render
from warp_windows_compat import enable


def read_ply(path):
    names=[];count=None
    with path.open('rb') as f:
        while True:
            line=f.readline().decode('ascii').strip()
            if line.startswith('element vertex'):count=int(line.split()[-1])
            if line.startswith('property float'):names.append(line.split()[-1])
            elif line.startswith('property '):raise ValueError('Unexpected PLY property')
            if line=='end_header':break
        return np.fromfile(f,dtype=[(n,'<f4') for n in names],count=count)


def main():
    started=time.perf_counter();enable();wp.init();device='cuda:0'
    out=ROOT/'outputs'/'ficus_short';out.mkdir(parents=True,exist_ok=True)
    source=ROOT/'inputs'/'ficus_whitebg-trained'/'point_cloud'/'iteration_30000'/'point_cloud.ply'
    data=read_ply(source)
    count_before=len(data)
    alpha=1/(1+np.exp(-data['opacity'].astype(float)))
    keep=alpha>.02
    data=data[keep];alpha=alpha[keep]
    xyz=np.column_stack([data[k] for k in 'xyz']).astype(float)
    origin=(xyz.min(0)+xyz.max(0))/2
    scale=1/np.ptp(xyz,axis=0).max()
    x=((xyz-origin)*scale+1).astype(np.float32)
    scales=np.exp(np.column_stack([data[f'scale_{i}'] for i in range(3)]).astype(float))*scale
    quat=np.column_stack([data[f'rot_{i}'] for i in range(4)]).astype(float)
    quat/=np.linalg.norm(quat,axis=1)[:,None]
    w,qx,qy,qz=quat.T
    R=np.empty((len(x),3,3))
    R[:,0,0]=1-2*(qy*qy+qz*qz);R[:,0,1]=2*(qx*qy-w*qz);R[:,0,2]=2*(qx*qz+w*qy)
    R[:,1,0]=2*(qx*qy+w*qz);R[:,1,1]=1-2*(qx*qx+qz*qz);R[:,1,2]=2*(qy*qz-w*qx)
    R[:,2,0]=2*(qx*qz-w*qy);R[:,2,1]=2*(qy*qz+w*qx);R[:,2,2]=1-2*(qx*qx+qy*qy)
    cov0=((R*scales[:,None,:])@(R*scales[:,None,:]).transpose(0,2,1)).astype(np.float32)
    packed=cov0[:,[0,0,0,1,1,2],[0,1,2,1,2,2]].copy()
    colors=np.clip(.5+.28209479177387814*np.column_stack([data[f'f_dc_{i}'] for i in range(3)]),0,1)
    config=json.loads((REPO/'config'/'ficus_config.json').read_text())
    grid=50;grid_lim=2.;dx=grid_lim/grid
    cell=np.floor(x/dx).astype(int)
    _,inv,counts=np.unique(cell,axis=0,return_inverse=True,return_counts=True)
    volume=(dx**3/counts[inv]).astype(np.float32)
    sim=MPM_Simulator_WARP(len(x),n_grid=grid,grid_lim=grid_lim,device=device)
    sim.mpm_state.particle_x=wp.array(x,dtype=wp.vec3,device=device)
    sim.mpm_state.particle_vol=wp.array(volume,dtype=float,device=device)
    sim.mpm_state.particle_init_cov=wp.array(packed.reshape(-1),dtype=float,device=device)
    wp.launch(set_mat33_to_identity,dim=len(x),inputs=[sim.mpm_state.particle_F_trial],device=device)
    params={k:config[k] for k in ('E','nu','material','density','g','grid_v_damping_scale','rpic_damping','additional_material_params')}
    sim.set_parameters_dict(params,device=device);sim.finalize_mu_lam(device=device)
    bc=config['boundary_conditions'][0]
    sim.set_velocity_on_cuboid(bc['point'],wp.vec3(bc['size']),bc['velocity'],start_time=bc['start_time'],end_time=bc['end_time'],reset=bc['reset'])
    impulse=config['boundary_conditions'][1]
    dt=config['substep_dt']
    sim.add_impulse_on_particles(impulse['force'],dt,num_dt=impulse['num_dt'],start_time=impulse['start_time'],device=device)
    mass0=float(sim.mpm_state.particle_mass.numpy().sum())
    rng=np.random.default_rng(20261101)
    sample=np.sort(rng.choice(len(x),min(6000,len(x)),replace=False))
    frames=[];snapshots=[];covsnap=[];times=[];cov_error=[];gpu_snap=[]
    steps=1200
    print(f'Ficus: {count_before} raw, {len(x)} retained physical Gaussians; {steps} CUDA steps',flush=True)
    for step in range(steps+1):
        if step%100==0:
            wp.launch(compute_cov_from_F,dim=len(x),inputs=[sim.mpm_state,sim.mpm_model],device=device)
            xx=sim.mpm_state.particle_x.numpy()
            F=sim.mpm_state.particle_F_trial.numpy()
            cov=unpack(sim.mpm_state.particle_cov.numpy().reshape(-1,6))
            assert np.isfinite(xx).all() and np.isfinite(F).all() and np.isfinite(cov).all()
            independent=F[sample]@cov0[sample]@F[sample].transpose(0,2,1)
            error=float(np.linalg.norm(independent-cov[sample])/np.linalg.norm(independent))
            assert error<2e-5,error
            cov_error.append(error)
            snapshots.append(xx[sample]);covsnap.append(cov[sample]);times.append(step*dt)
            frames.append(render(xx[sample],cov[sample],colors[sample],step*dt,'Ficus: sampled diagnostic view',limits=(.35,1.65,.35,1.65),size=360,opacity=alpha[sample]))
            try:gpu_snap.append(subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],text=True).strip())
            except Exception:pass
            print(f'step={step}, covariance relative error={error:.3e}, GPU memory MiB={gpu_snap[-1:]!s}',flush=True)
        if step<steps:sim.p2g2p(step,dt,device=device)
    displacement=np.linalg.norm(xx-x,axis=1)
    assert np.max(displacement)>1e-5
    assert np.isclose(float(sim.mpm_state.particle_mass.numpy().sum()),mass0,rtol=1e-6)
    frames[0].save(out/'ficus_diagnostic.gif',save_all=True,append_images=frames[1:],duration=100,loop=0)
    frames[0].save(out/'initial.png');frames[-1].save(out/'final.png')
    np.savez_compressed(out/'all_gaussians_initial_final.npz',initial_position=x,final_position=xx,final_F=F,
                        initial_covariance=cov0,final_covariance=cov,volume=volume,opacity=alpha,
                        original_origin=origin,scale=scale)
    np.savez_compressed(out/'sampled_trajectory.npz',indices=sample,time_s=times,positions=snapshots,covariance=covsnap)
    metrics=dict(scope='official pretrained Ficus all-retained-particle short MPM simulation; sampled local diagnostic renderer',
          all_checks_passed=True,raw_gaussians=count_before,simulated_gaussians=len(x),render_sample=len(sample),
          steps=steps,dt_s=dt,simulation_duration_s=steps*dt,grid=grid,grid_limit=grid_lim,
          initial_total_mass=mass0,max_displacement_simulation_units=float(displacement.max()),mean_displacement=float(displacement.mean()),
          covariance_relative_error_max=max(cov_error),sampled_total_gpu_memory_MiB=gpu_snap,
          model_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),model_url='https://drive.google.com/uc?id=1zic8PNxUsYESyrVZ8Ywy-FxpmQ01PGpe',
          adaptations=['NumPy equivalent normalization, quaternion covariance and cell-count volume','no Taichi filling; official ficus config has none','shortened 0.12 s vs original 5 s','6000 fixed sampled diagnostic render; all retained particles simulated','orthographic DC color renderer instead of official perspective SH rasterizer'],
          elapsed_s=time.perf_counter()-started)
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    (ROOT/'docs'/'FICUS_RESULTS.md').write_text(f'''# 官方 Ficus 模型短时运行

已下载官方脚本提供的 Ficus 模型，原始 {count_before} 个高斯，按原阈值 opacity>0.02 保留 {len(x)} 个，全部参与官方 Warp MPM 模拟。

## 配置与结果

使用官方 ficus_config.json 的 E、ν、密度、附加区域材料、固定底部、单步外力和网格速度阻尼。网格默认 50³、范围 [0,2]³、dt={dt} s；缩短为 {steps} 步，即 {steps*dt:.2f} s，而原配置是 125×0.04=5 s。
最大位置变化 {displacement.max():.6f}（归一化模拟坐标）；采样协方差公式相对误差最大 {max(cov_error):.3e}；所有高斯的位置、F、Σ 有限，质量不变。
GPU 采样总占用（包含其他进程和驱动）为 {gpu_snap} MiB，不能当作精确进程峰值。

## 适配与限制

预处理用 NumPy 等价实现包围盒中心缩放、四元数协方差、每格体积按粒子数分配，替代硬编码 CUDA/Taichi 的辅助入口；物理步进与协方差核来自未改动的官方代码。
动画固定抽取 {len(sample)} 个点，用本地正交 DC 颜色高斯渲染器做诊断。抽样仅影响显示，不影响参与物理模拟的高斯数。没有运行原透视相机/SH/CUDA 光栅器，也没有论文画质指标，不能将该动画标为原官方渲染结果。
`all_gaussians_initial_final.npz` 保留全量初末状态；`sampled_trajectory.npz` 保留显示子集每帧状态，`metrics.json` 包含模型 SHA256、来源和全部适配项。
''',encoding='utf-8')
    print(json.dumps(metrics,indent=2),flush=True)


if __name__=='__main__':main()
