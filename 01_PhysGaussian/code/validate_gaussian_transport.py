"""Independent invariants for the unchanged published Gaussian transport kernels."""
import os
import sys
import json
import hashlib
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
os.environ.setdefault('MPLCONFIGDIR', str(WORK/'reproduction/cache/matplotlib'))
os.environ.setdefault('CUDA_CACHE_PATH', str(WORK/'reproduction/cache/cuda'))
sys.dont_write_bytecode = True
REPO = Path('/opt/3dgs-runtime/PhysGaussian-source')
assert REPO.samefile(ROOT/'code/PhysGaussian')
sys.path[:0] = [str(REPO), str(REPO/'gaussian-splatting')]
import numpy as np
from scipy.linalg import expm, polar
from scipy.spatial.transform import Rotation
import torch
import warp as wp
wp.config.kernel_cache_dir = str(WORK/'reproduction/cache/warp')
from mpm_solver_warp.mpm_solver_warp import MPM_Simulator_WARP
from mpm_solver_warp.mpm_utils import compute_cov_from_F, compute_R_from_F, g2p
from utils.render_utils import convert_SH
from utils.sh_utils import eval_sh

PAIRS = ((0,0),(0,1),(0,2),(1,1),(1,2),(2,2))


def packed(a):
    return np.stack([a[:,i,j] for i,j in PAIRS],axis=-1).astype(np.float32)


def unpack(a):
    a=np.asarray(a).reshape(-1,6);result=np.zeros((len(a),3,3))
    for k,(i,j) in enumerate(PAIRS):result[:,i,j]=result[:,j,i]=a[:,k]
    return result


def relative(a,b):
    return float(np.linalg.norm(a-b)/np.linalg.norm(b))


def main():
    wp.init();torch.set_grad_enabled(False);torch.set_num_threads(2)
    device='cuda:0';out=ROOT/'outputs/gaussian_transport';out.mkdir(exist_ok=True)
    rng=np.random.default_rng(20261103);n=96
    q=Rotation.random(n,random_state=rng).as_matrix()
    axes=np.exp(rng.uniform(-1.5,1.,(n,3)))
    cov0=np.einsum('nij,nj,nkj->nik',q,axes,q)*1e-4
    rotation=Rotation.random(n,random_state=rng).as_matrix()
    stretch=np.einsum('nij,nj,nkj->nik',q,rng.uniform(.6,1.6,(n,3)),q)
    F=rotation@stretch
    sim=MPM_Simulator_WARP(n,n_grid=16,grid_lim=1.,device=device)
    sim.mpm_state.particle_init_cov=wp.array(packed(cov0).reshape(-1),dtype=float,device=device)
    sim.mpm_state.particle_F_trial=wp.array(F.astype(np.float32),dtype=wp.mat33,device=device)
    wp.launch(compute_cov_from_F,n,inputs=[sim.mpm_state,sim.mpm_model],device=device)
    wp.launch(compute_R_from_F,n,inputs=[sim.mpm_state,sim.mpm_model],device=device)
    actual=unpack(sim.mpm_state.particle_cov.numpy());inverse_R=sim.mpm_state.particle_R.numpy()
    reference=F@cov0@F.transpose(0,2,1)
    # Volume and metric invariants give independent checks beyond entrywise formula equality.
    delta=rng.normal(size=(n,3));mapped=np.einsum('nij,nj->ni',F,delta)
    ma0=np.einsum('ni,nij,nj->n',delta,np.linalg.inv(cov0),delta)
    mat=np.einsum('ni,nij,nj->n',mapped,np.linalg.inv(actual),mapped)
    determinant_reference=np.linalg.det(F)**2*np.linalg.det(cov0)
    polar_reference=np.stack([polar(f)[0].T for f in F])
    values=dict(covariance_relative_L2=relative(actual,reference),
        determinant_relative_L2=relative(np.linalg.det(actual),determinant_reference),
        gaussian_exponent_relative_L2=relative(mat,ma0),
        inverse_polar_rotation_relative_L2=relative(inverse_R,polar_reference),
        minimum_covariance_eigenvalue=float(np.linalg.eigvalsh(actual).min()),
        maximum_rotation_orthogonality_error=float(np.max(np.abs(inverse_R@inverse_R.transpose(0,2,1)-np.eye(3)))))
    for key in ('covariance_relative_L2','determinant_relative_L2','gaussian_exponent_relative_L2','inverse_polar_rotation_relative_L2','maximum_rotation_orthogonality_error'):
        assert values[key]<2e-5,(key,values[key])
    assert values['minimum_covariance_eigenvalue']>0
    # Rotating object and camera together must preserve the degree-3 SH radiance.
    pos=rng.normal(size=(n,3));sh=rng.normal(scale=.03,size=(n,16,3))
    rotate=rotation[0];translation=np.array([.2,-.1,.3]);camera=np.array([2.,3.,4.])
    to=lambda a:torch.tensor(a,dtype=torch.float32,device=device)
    pc=SimpleNamespace(active_sh_degree=3,max_sh_degree=3)
    base=convert_SH(to(sh),SimpleNamespace(camera_center=to(camera)),pc,to(pos))
    transformed=convert_SH(to(sh),SimpleNamespace(camera_center=to(rotate@camera+translation)),pc,
        to(pos@rotate.T+translation),to(np.repeat(rotate.T[None],n,axis=0)))
    values['rigid_camera_object_SH_relative_L2']=relative(transformed.cpu().numpy(),base.cpu().numpy())
    assert values['rigid_camera_object_SH_relative_L2']<1e-6
    # The actual g2p branch implements explicit-Euler Eq.(10). Compare with exp(t L).
    L=np.array([[.3,-1.2,.1],[1.2,-.2,.15],[0.,.1,-.1]])
    T=.2;initial=np.diag([1.,2.,4.])*1e-4
    exact=expm(T*L)@initial@expm(T*L).T
    incremental=[]
    for dt in (.01,.005,.0025):
        s=MPM_Simulator_WARP(1,n_grid=16,grid_lim=1.,device=device)
        s.mpm_model.update_cov_with_F=True
        s.mpm_state.particle_x=wp.array(np.array([[.5,.5,.5]],np.float32),dtype=wp.vec3,device=device)
        s.mpm_state.particle_cov=wp.array(packed(initial[None]).reshape(-1),dtype=float,device=device)
        s.mpm_state.particle_F=wp.array(np.eye(3,dtype=np.float32)[None],dtype=wp.mat33,device=device)
        grid=np.stack(np.meshgrid(*([np.arange(16)/16.]*3),indexing='ij'),axis=-1)
        velocity=(grid-.5)@L.T
        s.mpm_state.grid_v_out=wp.array(velocity.astype(np.float32),dtype=wp.vec3,device=device)
        for _ in range(round(T/dt)):
            wp.launch(g2p,1,inputs=[s.mpm_state,s.mpm_model,dt],device=device)
            s.mpm_state.particle_F=s.mpm_state.particle_F_trial
        result=unpack(s.mpm_state.particle_cov.numpy())[0]
        incremental.append(dict(dt=dt,steps=round(T/dt),relative_error=relative(result,exact),minimum_eigenvalue=float(np.linalg.eigvalsh(result).min())))
    ratios=[incremental[i]['relative_error']/incremental[i+1]['relative_error'] for i in (0,1)]
    assert all(1.8<r<2.2 for r in ratios),ratios
    assert all(r['minimum_eigenvalue']>0 for r in incremental)
    np.savez_compressed(out/'reference_arrays.npz',initial_covariances=cov0,deformation_gradients=F,
        actual_covariances=actual,reference_covariances=reference,actual_inverse_rotations=inverse_R,reference_inverse_rotations=polar_reference,
        original_SH_colors=base.cpu().numpy(),transformed_SH_colors=transformed.cpu().numpy(),velocity_gradient=L,incremental_exact=exact)
    sources={p:hashlib.sha256((REPO/p).read_bytes()).hexdigest() for p in ('mpm_solver_warp/mpm_utils.py','utils/render_utils.py')}
    result=dict(all_checks_passed=True,random_cases=n,checks=values,incremental=incremental,
        incremental_error_reduction_ratios=ratios,source_sha256=sources,
        scope='PhysGaussian Eqs.8-10: actual unchanged CUDA kernels and SH function; analytic invariants and time-step convergence, not a full benchmark')
    payload=json.dumps(result,indent=2);(out/'metrics.json').write_text(payload);(ROOT/'docs/gaussian-transport-metrics.json').write_text(payload)
    report=f'''# 高斯协方差、旋转与增量输运独立验证

实际调用未修改的 compute_cov_from_F、compute_R_from_F、g2p 和 convert_SH，对应论文 §3.4–3.6、式(8)–(10)。96 组正定协方差与正行列式变形，独立检查高斯指数不变、体积行列式规律、SciPy 极分解和物体/相机同步旋转后的三阶 SH 颜色。全部通过；详细误差见 [指标](gaussian-transport-metrics.json)。

增量分支在给定仿射速度场下与矩阵指数精确解对照，时间步 0.01/0.005/0.0025 秒，终点 0.2 秒。误差减半比为 {ratios[0]:.5f}、{ratios[1]:.5f}，符合显式 Euler 一阶收敛。正定性只在此步长和速度场验证，不声称任意大时间步都保持正定。默认完整场景使用总变形梯度分支；本实验额外覆盖原代码的增量开关。

原代码 compute_R_from_F 保存的是极旋转的转置，供 SH 逆向旋转视线使用，不能把它当正向旋转误判。参考数组保存在 [NPZ](../outputs/gaussian_transport/reference_arrays.npz)。本实验不替代论文变形图像基准或缺失 snow 材料。

重跑：在已配置 Linux physgaussian Conda 中执行 code/validate_gaussian_transport.py；入口 code/run_transport_audit.sh。代码、缓存与输出均位于项目内，仅只读使用现有 ASCII 源码软链接。
'''
    (ROOT/'docs/GAUSSIAN_TRANSPORT.md').write_text(report,encoding='utf-8');print(payload,flush=True)


if __name__=='__main__':main()
