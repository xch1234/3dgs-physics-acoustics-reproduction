"""Small PAT-method reproduction: FEM -> indirect BEM -> offset fit -> audio.

Locally authored implementation of PAT 2006 sections 3, 4.1-4.3.1.
Not the paper's original code, multilevel algorithm, or benchmark scenes.
Time convention exp(+i omega t), outgoing exp(-i k r).
"""
import os
for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[name] = '1'
os.environ['MPLBACKEND'] = 'Agg'
import json
import time
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
from scipy.special import spherical_jn, spherical_yn, sph_harm
from scipy.linalg import solve, lstsq, svd
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'pat_pipeline'
FEM = ROOT / 'inputs' / 'official_fem_result.npz'


def sphere_points(n, radius, phase=0):
    j = np.arange(n) + 0.5
    z = 1 - 2*j/n
    angle = j*np.pi*(3-np.sqrt(5)) + phase
    return radius * np.c_[np.sqrt(1-z*z)*np.cos(angle), np.sqrt(1-z*z)*np.sin(angle), z]


def refine(vertices, faces, values=None, radius=None):
    vs = list(vertices)
    vals = list(values) if values is not None else None
    edges, fs = {}, []
    def midpoint(a, b):
        key = tuple(sorted((int(a), int(b))))
        if key not in edges:
            p = (vertices[a]+vertices[b])/2
            if radius is not None:
                p *= radius / np.linalg.norm(p)
            edges[key] = len(vs)
            vs.append(p)
            if vals is not None:
                vals.append((values[a]+values[b])/2)
        return edges[key]
    for a,b,c in faces:
        ab,bc,ca = midpoint(a,b),midpoint(b,c),midpoint(c,a)
        fs.extend([[a,ab,ca],[ab,b,bc],[ca,bc,c],[ab,bc,ca]])
    return np.asarray(vs), np.asarray(fs), None if vals is None else np.asarray(vals)


def panels(vertices, faces):
    tri = vertices[faces]
    cross = np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    area = np.linalg.norm(cross,axis=1)/2
    normal = cross/(2*area[:,None])
    center = tri.mean(axis=1)
    # All inputs used here are convex and centered at zero.
    normal *= np.where(np.einsum('ij,ij->i', normal, center)>0,1,-1)[:,None]
    bary = np.array([[2/3,1/6,1/6],[1/6,2/3,1/6],[1/6,1/6,2/3]])
    quad = np.einsum('qv,pvd->pqd', bary, tri)
    return center, normal, area, quad


def bem_operator(mesh, k):
    center, normal, area, quad = mesh
    count = len(area)
    matrix = np.zeros((count,count),dtype=complex)
    # Exterior normal derivative of a single-layer potential: -I/2 + K'.
    # Flat-panel self K' is zero; 3-point triangle quadrature for off-diagonal terms.
    for q in range(3):
        delta = center[:,None,:]-quad[None,:,q,:]
        r = np.linalg.norm(delta,axis=2)
        np.fill_diagonal(r,1)
        normal_dot = np.einsum('ijd,id->ij',delta,normal)
        kernel = np.exp(-1j*k*r)*(-1j*k*r-1)*normal_dot/(4*np.pi*r**3)
        np.fill_diagonal(kernel,0)
        matrix += kernel*area[None,:]/3
    matrix -= np.eye(count)/2
    return matrix


def bem_pressure(points, mesh, k, density):
    _,_,area,quad = mesh
    result=[]
    for block in np.array_split(points,max(1,int(np.ceil(len(points)/256)))):
        G = np.zeros((len(block),len(area)),dtype=complex)
        for q in range(3):
            r = np.linalg.norm(block[:,None,:]-quad[None,:,q,:],axis=2)
            G += np.exp(-1j*k*r)/(4*np.pi*r)*area[None,:]/3
        result.append(G@density)
    return np.concatenate(result)


def hankel(l, x, derivative=False):
    return spherical_jn(l,x,derivative)-1j*spherical_yn(l,x,derivative)


def multipoles(points, source, k):
    d = points-source
    r = np.linalg.norm(d,axis=1)
    azimuth = np.arctan2(d[:,1],d[:,0])
    polar = np.arccos(np.clip(d[:,2]/r,-1,1))
    return np.column_stack([hankel(l,k*r)*sph_harm(m,l,azimuth,polar)
                            for l in range(2) for m in range(-l,l+1)])


def fit_pat(points, target, candidates, k, weights, tolerance=.02, max_sources=24):
    blocks=[multipoles(points,c,k) for c in candidates]
    weighted=[b*weights[:,None] for b in blocks]
    subspaces=[]
    for b in weighted:
        u,s,_=svd(b,full_matrices=False)
        subspaces.append(u[:,s>s[0]*1e-6])
    b=target*weights
    residual=b.copy()
    selected=[]
    history=[1.0]
    for _ in range(max_sources):
        scores=[np.linalg.norm(u.conj().T@residual)**2 if i not in selected else -1
                for i,u in enumerate(subspaces)]
        selected.append(int(np.argmax(scores)))
        A=np.concatenate([weighted[i] for i in selected],axis=1)
        # Truncated SVD matches the paper's relative threshold 1e-6.
        coeff,_,rank,s=lstsq(A,b,cond=1e-6,lapack_driver='gelsd')
        residual=b-A@coeff
        history.append(float(np.linalg.norm(residual)/np.linalg.norm(b)))
        if history[-1] < tolerance:
            break
    return candidates[selected],coeff,dict(relative_fit_history=history,sources=len(selected),
             complex_coefficients=len(coeff),svd_rank=int(rank),fit_relative_L2=history[-1],svd_relative_cutoff=1e-6)


def pat_pressure(points, centers, coeff, k):
    return np.concatenate([multipoles(points,c,k) for c in centers],axis=1)@coeff


def sphere_check():
    radius=.05
    gold=(1+np.sqrt(5))/2
    v=np.array([(0,a,b*gold) for a in (-1,1) for b in (-1,1)] +
               [(a,b*gold,0) for a in (-1,1) for b in (-1,1)] +
               [(b*gold,0,a) for a in (-1,1) for b in (-1,1)],float)
    v*=radius/np.linalg.norm(v[0])
    f=ConvexHull(v).simplices
    k=2*np.pi*400/343
    query=sphere_points(96,.3)
    expected=hankel(0,k*.3)/(k*hankel(0,k*radius,True))
    checks=[]
    for level in (1,2,3):
        v,f,_=refine(v,f,radius=radius)
        mesh=panels(v,f)
        A=bem_operator(mesh,k)
        sigma=solve(A,np.ones(len(f)),check_finite=False)
        p=bem_pressure(query,mesh,k,sigma)
        error=float(np.linalg.norm(p-expected)/np.linalg.norm(np.full(len(p),expected)))
        checks.append(dict(triangles=len(f),relative_complex_pressure_error=error,
                           linear_residual=float(np.linalg.norm(A@sigma-1)/np.sqrt(len(f)))))
    assert checks[-1]['relative_complex_pressure_error'] < .03, checks
    # Coarsest polyhedron can exhibit cancellation between geometry and quadrature
    # errors; do not assume strict monotonicity from an accidental coarse match.
    assert checks[-1]['relative_complex_pressure_error'] < checks[-2]['relative_complex_pressure_error'], checks
    return checks


def beam_surface(data):
    vertices=data['vertices_m']
    modes=np.zeros((len(vertices)*3,6))
    modes[data['free_dofs']]=data['clamped_modes_mass_normalized'][:,:6]
    modes=modes.reshape(-1,3,6)
    voxel=data['voxel']
    coordinates=np.rint((vertices/.12+.5)*6).astype(int)
    vertex_map={tuple(x):i for i,x in enumerate(coordinates)}
    faces=[]
    for cell in np.argwhere(voxel):
        for axis in range(3):
            for side in (0,1):
                near=cell.copy();near[axis]+=2*side-1
                if np.all(near>=0) and np.all(near<6) and voxel[tuple(near)]==1:
                    continue
                others=[j for j in range(3) if j!=axis]
                square=[]
                for a,b in ((0,0),(1,0),(1,1),(0,1)):
                    corner=cell.copy();corner[axis]+=side
                    corner[others[0]]+=a;corner[others[1]]+=b
                    square.append(vertex_map[tuple(corner)])
                faces.extend([[square[0],square[1],square[2]],[square[0],square[2],square[3]]])
    return vertices,np.asarray(faces),modes


def main():
    started=time.perf_counter()
    OUT.mkdir(parents=True,exist_ok=True)
    if not FEM.exists():
        raise FileNotFoundError('Missing inputs/official_fem_result.npz; regenerate via 03_NeuralSound/run.ps1 and copy this documented shared input')
    analytic_checks=sphere_check()
    print('Analytic pulsating-sphere validation:',analytic_checks,flush=True)
    data=np.load(FEM)
    v,f,modes=beam_surface(data)
    v,f,modes=refine(v,f,modes)
    mesh=panels(v,f)
    offset=sphere_points(384,.11)
    weights=np.full(len(offset),np.sqrt(4*np.pi*.11**2/len(offset)))
    validation=np.r_[sphere_points(180,.17,.63),sphere_points(180,.3,1.23)]
    rng=np.random.default_rng(20261101)
    candidates=rng.uniform([-0.055,-0.016,-0.016],[0.055,0.016,0.016],(80,3))
    listeners=np.array([[.3,0,0],[0,.3,0],[0,0,.3]])
    rho=1.225
    frequencies=data['frequencies_Hz'][:6]
    transfer_bem=np.zeros((3,6),complex)
    transfer_pat=np.zeros((3,6),complex)
    results=[]
    circle_angle=np.linspace(0,2*np.pi,181)
    circle=.3*np.c_[np.cos(circle_angle),np.sin(circle_angle),np.zeros(len(circle_angle))]
    directivity=[]
    for j,freq in enumerate(frequencies):
        omega=2*np.pi*freq;k=omega/343
        normal_mode=np.einsum('ij,ij->i',modes[f,:,j].mean(axis=1),mesh[1])
        # v=i*w*phi*q -> dp/dn=-i*w*rho*v=rho*w^2*phi*q, with q=1.
        g=rho*omega**2*normal_mode
        A=bem_operator(mesh,k)
        sigma=solve(A,g,check_finite=False)
        residual=float(np.linalg.norm(A@sigma-g)/np.linalg.norm(g))
        pressure=bem_pressure(offset,mesh,k,sigma)
        centers,coeff,fit=fit_pat(offset,pressure,candidates,k,weights)
        ref=bem_pressure(validation,mesh,k,sigma)
        approx=pat_pressure(validation,centers,coeff,k)
        error=float(np.linalg.norm(approx-ref)/np.linalg.norm(ref))
        assert residual<1e-10 and error<.08,(j,residual,error,fit)
        assert fit['fit_relative_L2']<.05,fit
        transfer_bem[:,j]=bem_pressure(listeners,mesh,k,sigma)
        transfer_pat[:,j]=pat_pressure(listeners,centers,coeff,k)
        directivity.append((bem_pressure(circle,mesh,k,sigma),pat_pressure(circle,centers,coeff,k)))
        np.savez_compressed(OUT/f'mode_{j+1:02d}_transfer.npz',centers_m=centers,coefficients=coeff,k_per_m=k,
                            bem_single_layer_density=sigma,offset_points_m=offset,offset_pressure=pressure,
                            validation_points_m=validation,validation_bem_pressure=ref,validation_pat_pressure=approx)
        result=dict(mode=j+1,frequency_Hz=float(freq),bem_residual=residual,validation_relative_complex_L2=error,**fit)
        results.append(result)
        print('mode',j+1,'sources',fit['sources'],'held-out relative error',error,flush=True)

    # Mesh refinement sensitivity: strongest radiating lowest mode, independent of fit.
    vc,fc,mc=beam_surface(data)
    coarse=panels(vc,fc)
    w=2*np.pi*frequencies[0];k=w/343
    gc=rho*w*w*np.einsum('ij,ij->i',mc[fc,:,0].mean(axis=1),coarse[1])
    sigmac=solve(bem_operator(coarse,k),gc)
    pcoarse=bem_pressure(validation,coarse,k,sigmac)
    fine=np.load(OUT/'mode_01_transfer.npz')['validation_bem_pressure']
    mesh_difference=float(np.linalg.norm(pcoarse-fine)/np.linalg.norm(fine))
    np.savez_compressed(OUT/'surface_mesh.npz',vertices_m=v,faces=f,normals=mesh[1],areas_m2=mesh[2],listeners_m=listeners)

    fs=48000;t=np.arange(fs*3)/fs
    # Local impulse on the far x corner in the y direction, 0.001 N s.
    input_vertices=data['vertices_m']
    hit=int(np.argmax(input_vertices@np.array([1,.1,.01])))
    full_modes=np.zeros((len(input_vertices)*3,6))
    full_modes[data['free_dofs']]=data['clamped_modes_mass_normalized'][:,:6]
    gmodal=full_modes.reshape(-1,3,6)[hit,1,:]*.001
    responses=[]
    for j,freq in enumerate(frequencies):
        w=2*np.pi*freq;d=(30+1e-6*w*w)/2;wd=np.sqrt(w*w-d*d)
        responses.append(gmodal[j]/wd*np.exp(-d*t)*np.sin(wd*t))
    q=np.array(responses)
    pressure_bem=np.abs(transfer_bem)@q
    pressure_pat=np.abs(transfer_pat)@q
    # PAT paper section 3 uses |p(x)| q(t), discarding transfer phase for playback.
    gain=.85/max(np.max(np.abs(pressure_bem)),np.max(np.abs(pressure_pat)))
    fade=np.ones(len(t));fade[-960:]=np.linspace(1,0,960)
    for label,signals in [('bem',pressure_bem),('pat',pressure_pat)]:
        for i,axis in enumerate('xyz'):
            wav=np.rint(signals[i]*gain*fade*32767).astype(np.int16)
            assert np.max(np.abs(wav.astype(np.int32)))<32767
            wavfile.write(OUT/f'{label}_listener_{axis}.wav',fs,wav)
            sr,read=wavfile.read(OUT/f'{label}_listener_{axis}.wav')
            assert sr==fs and np.array_equal(read,wav)
    np.savez_compressed(OUT/'pressure_audio_raw.npz',time_s=t,pressure_bem_Pa=pressure_bem,pressure_pat_Pa=pressure_pat,
                        modal_response=q,transfer_bem=transfer_bem,transfer_pat=transfer_pat,common_gain=gain)
    assert np.isfinite(pressure_pat).all()
    audio_error=float(np.linalg.norm(pressure_pat-pressure_bem)/np.linalg.norm(pressure_bem))

    fig,ax=plt.subplots(1,3,figsize=(15,4.5),layout='constrained')
    ax[0].loglog([r['triangles'] for r in analytic_checks],[r['relative_complex_pressure_error'] for r in analytic_checks],'o-')
    ax[0].set(xlabel='Boundary triangles',ylabel='Relative complex pressure L2 error',title='BEM vs analytic pulsating sphere (400 Hz)')
    for r in results:
        ax[1].semilogy(range(len(r['relative_fit_history'])),r['relative_fit_history'],label=f"Mode {r['mode']}")
    ax[1].set(xlabel='Selected dipole source centers',ylabel='Relative weighted pressure residual',title='PAT greedy placement on offset sphere')
    ax[1].legend(fontsize=8)
    ax[2].bar(np.arange(1,7),[r['validation_relative_complex_L2']*100 for r in results])
    ax[2].set(xlabel='Mode index',ylabel='Relative complex pressure L2 error (%)',title='Held-out exterior queries: PAT vs BEM')
    fig.suptitle('Small PAT-method reproduction | locally generated beam; not paper benchmark')
    fig.savefig(OUT/'validation.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(12,4),subplot_kw={'projection':'polar'},layout='constrained')
    for idx,ax in enumerate(axs):
        pr,pa=directivity[idx]
        norm=max(np.max(np.abs(pr)),1e-30)
        ax.plot(circle_angle,np.abs(pr)/norm,label='BEM')
        ax.plot(circle_angle,np.abs(pa)/norm,'--',label='PAT')
        ax.set_title(f'Mode {idx+1}: {frequencies[idx]:.1f} Hz',pad=18)
        ax.set_rlim(0,1.1)
        ax.legend(loc='lower right',fontsize=8)
    fig.suptitle('XY listening circle r=0.30 m | angle (degrees), amplitude / BEM maximum')
    fig.savefig(OUT/'directivity.png',dpi=160);plt.close(fig)
    metrics=dict(scope='local PAT core pipeline, sections 3 and 4.1-4.3.1; not full paper results',all_checks_passed=True,
                 convention='exp(+i omega t), outgoing h_l^(2); rho=1.225 kg/m3, c=343 m/s',
                 bem='indirect single-layer constant flat triangles, exterior Neumann collocation, 3-point quadrature',
                 panels=len(f),sphere_validation=analytic_checks,first_mode_coarse_fine_relative_difference=mesh_difference,
                 mode_results=results,offset_radius_m=.11,validation_radii_m=[.17,.3],listeners_m=listeners.tolist(),
                 impulse_vertex=hit,impulse_direction='y',impulse_N_s=.001,audio_relative_L2=audio_error,common_playback_gain=gain,
                 limitation='six coarse FEM modes; no multilevel placement, thin-shell benchmark, high-frequency treatment or speedup claim; audio ignores transfer phase per paper',
                 elapsed_s=time.perf_counter()-started)
    (OUT/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    (ROOT/'docs'/'RESULTS.md').write_text(f'''# PAT 小型方法复现结果

完成一条自建小场景链路：官方 FEM 模态输入 → 间接 BEM 外辐射 → 包围偏移面采样 → 四项球面多极子贪心选择 → 截断 SVD 拟合 → 三个听者位置的声音。
对应论文 §3、§4.1–4.3.1；不是原作者程序、论文全场景或多层加速复现。

## 实际指标

- 边界面片数：{len(f)}；六个 FEM 模态频率：{', '.join(f'{x:.3f}' for x in frequencies)} Hz。
- 脉动球解析校验：80/320/1280 面片的复声压相对误差分别为 {', '.join(f"{r['relative_complex_pressure_error']:.3%}" for r in analytic_checks)}。
- 各模态独立外部点 PAT 相对 BEM 误差：{', '.join(f"{r['validation_relative_complex_L2']:.3%}" for r in results)}。
- 各模态多极子中心数：{[r['sources'] for r in results]}，每中心四个复系数。
- 第一模态粗/细 BEM 网格差异：{mesh_difference:.3%}。这是离散敏感性，不是相对真实物体的误差。
- 三听者合计音频相对 BEM 误差：{audio_error:.3%}；共享播放增益，六段音频均回读无削波。

## 查看

`outputs/pat_pipeline/validation.png` 展示解析校验、拟合残差和独立点误差；`directivity.png` 展示方向图。
`pat_listener_x/y/z.wav` 是三个听者的 PAT 音频，`bem_listener_x/y/z.wav` 是 BEM 参考。
未经播放增益处理的声压、系数、网格、独立查询点和参数在对应 NPZ 与 metrics.json 中。

## 方法与边界

以 e^(+iωt) 为时间约定，使用 outgoing exp(-ikr) 核。由单位模态位移产生法向压力导数 ρω²(n·φ)。BEM 解 (-I/2+K')σ=g，再以单层势求空间压力。
解析球测试独立于梁的 FEM、边界离散与 PAT 拟合。平面自项 K'=0，其余用三点三角形积分；未实现高阶近奇异积分、CHIEF 或 Burton–Miller，因此不声称适用于任意高频或内共振情形。
偏移面采用包围半径 0.11 m 的球面，不是论文的距离场 marching cubes。源位置来自梁内部的固定随机候选池，使用论文子空间投影评分和全局 SVD 重拟合；不是逐轮重新采样或多层筛选。
每源含 l=0,1 四项，SVD 相对阈值 1e-6。独立查询点从未参与拟合。
声音按论文 §3 的 |p(x)|q(t) 近似合成，忽略传递相位；不是完整瞬态延迟求解。输入仅六个粗网格模态，不具备论文全频段音色或实验精度。
''',encoding='utf-8')
    print(json.dumps(metrics,indent=2),flush=True)


if __name__=='__main__':
    main()
