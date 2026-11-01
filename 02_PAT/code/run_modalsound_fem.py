"""Real ModalSound C++ assembly against independent linear-tetrahedron FEM."""
import hashlib
import itertools
import json
import subprocess
from pathlib import Path
import numpy as np
from scipy.linalg import eigh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]


def reference(vertices,tetrahedra,young,poisson,density):
    n=len(vertices)*3;K=np.zeros((n,n));M=np.zeros_like(K)
    lam=young*poisson/((1+poisson)*(1-2*poisson));mu=young/(2*(1+poisson))
    D=np.diag([2*mu]*3+[mu]*3);D[:3,:3]+=lam
    for tet in tetrahedra:
        v=vertices[tet];vol=np.linalg.det((v[1:]-v[0]).T)/6
        assert vol>0
        grads=np.linalg.inv(np.c_[np.ones(4),v])[1:,:].T
        B=np.zeros((6,12))
        for i,(x,y,z) in enumerate(grads):
            B[:,i*3:i*3+3]=[[x,0,0],[0,y,0],[0,0,z],[0,z,y],[z,0,x],[y,x,0]]
        indices=(tet[:,None]*3+np.arange(3)).ravel()
        K[np.ix_(indices,indices)]+=vol*B.T@D@B
        M[np.ix_(indices,indices)]+=density*vol/20*np.kron(np.ones((4,4))+np.eye(4),np.eye(3))
    return K,M


def load_matrix(path):
    with path.open() as f:n,nnz=map(int,f.readline().split())
    rows=np.loadtxt(path,skiprows=1);assert len(rows)==nnz
    a=np.zeros((n,n));i,j=rows[:,:2].astype(int).T;a[i,j]=rows[:,2]
    return a+np.triu(a,1).T


def main():
    out=ROOT/'outputs/modalsound_fem';out.mkdir(exist_ok=True,parents=True)
    shape=(7,3,3);vertices=np.array(list(itertools.product(*[np.arange(n)*.02 for n in shape])))
    index=lambda p:np.ravel_multi_index(tuple(p),shape)
    tetrahedra=[]
    for cell in itertools.product(range(6),range(2),range(2)):
        for order in itertools.permutations(range(3)):
            corner=np.array(cell);ids=[index(corner)]
            for direction in order:
                corner=corner.copy();corner[direction]+=1;ids.append(index(corner))
            if np.linalg.det((vertices[ids[1:]]-vertices[ids[0]]).T)<0:ids[2],ids[3]=ids[3],ids[2]
            tetrahedra.append(ids)
    tetrahedra=np.array(tetrahedra);young,nu,rho=3.5e9,.35,1050.
    Kref,Mref=reference(vertices,tetrahedra,young,nu,rho);records=[];frequency_sets=[]
    for name,fixed,scale in [('free',0,1),('fixed',9,1),('stiff',9,4)]:
        mesh=out/f'{name}.mesh.txt'
        with mesh.open('w') as f:
            f.write(f'{len(vertices)} {len(tetrahedra)} {fixed} {young*scale:.17g} {nu:.17g}\n')
            np.savetxt(f,vertices,fmt='%.17g');np.savetxt(f,tetrahedra,fmt='%d')
        subprocess.run([str(out/'assemble_fem'),str(mesh),str(out/name)],check=True)
        K=load_matrix(out/f'{name}.stiffness.txt');M=load_matrix(out/f'{name}.mass.txt')*rho
        # Upstream mass_mat is unit density; apply the physical density once.
        Kr=Kref[fixed*3:,fixed*3:]*scale;Mr=Mref[fixed*3:,fixed*3:]
        ke=np.linalg.norm(K-Kr)/np.linalg.norm(Kr);me=np.linalg.norm(M-Mr)/np.linalg.norm(Mr)
        assert ke<1e-11 and me<1e-12,(name,ke,me)
        E,U=eigh(K,M);skip=6 if not fixed else 0
        if not fixed:
            assert np.max(np.abs(E[:6]))<E[6]*1e-8
            for axis in range(3):
                translation=np.zeros(len(vertices)*3);translation[axis::3]=1
                assert np.isclose(translation@M@translation,.12*.04*.04*rho)
        E=E[skip:skip+12];U=U[:,skip:skip+12]
        rr=np.linalg.norm(K@U-(M@U)*E,axis=0)/(np.linalg.norm(K@U,axis=0)+np.linalg.norm((M@U)*E,axis=0))
        assert rr.max()<1e-9
        frequencies=np.sqrt(E)/(2*np.pi);frequency_sets.append(frequencies)
        np.savez_compressed(out/f'{name}_modes.npz',K=K,M=M,modes=U,eigenvalues=E,frequencies_Hz=frequencies,vertices=vertices,tetrahedra=tetrahedra)
        records.append(dict(case=name,fixed_vertices=fixed,young_modulus_Pa=young*scale,
            stiffness_relative_error=ke,mass_relative_error=me,max_relative_eigen_residual=float(rr.max()),frequencies_Hz=frequencies.tolist()))
    scaling=float(np.max(np.abs(frequency_sets[2]/frequency_sets[1]-2)))
    assert scaling<1e-10
    source=ROOT/'code/ModalSound/ModalSound/src'
    metrics=dict(scope='unchanged educational ModalSound C++ mass/stiffness assembly, not complete PAT author pipeline',
        all_checks_passed=True,vertices=len(vertices),tetrahedra=len(tetrahedra),density_kg_m3=rho,poisson_ratio=nu,
        total_mass_kg=.12*.04*.04*rho,records=records,young_times_four_frequency_ratio_error=scaling,
        sources={name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in ('deformable/fem.hpp','deformable/stvk.cpp','geometry/Tet.hpp')},
        notes=['official mass_mat stores unit-density mass; density applied once externally','independent Python linear tetrahedron B-transpose-D-B reference','six rigid modes checked in free body','not a hex-vs-tet convergence benchmark'])
    payload=json.dumps(metrics,indent=2);(out/'metrics.json').write_text(payload);(ROOT/'docs/modalsound-fem-metrics.json').write_text(payload)
    fig,ax=plt.subplots(figsize=(8,4),layout='constrained')
    for row in records:ax.plot(np.arange(1,13),row['frequencies_Hz'],'o-',label=row['case'])
    ax.set(xlabel='Elastic mode',ylabel='Frequency (Hz)',title='Actual ModalSound C++ FEM / local tetrahedral beam');ax.legend()
    fig.savefig(out/'frequencies.png',dpi=150);plt.close(fig)
    text=f'''# ModalSound 原始 C++ 四面体 FEM

实际编译和调用原 `DeformableFEM::mass_mat`、`stiffness_mat` 与 `StVKMaterial::stiffness_matrix`，未修改上游源码。外部 C++ 驱动提供网格和输出；独立 Python 参考使用线性四面体 BᵀDB 公式。

本地 0.12×0.04×0.04 m 梁，63 顶点、144 四面体，E=3.5 GPa、ν=0.35、ρ=1050。总质量 {metrics['total_mass_kg']:.6f} kg；自由体检查六个刚体零模态，固定体固定 x 最小面 9 顶点。原 mass_mat 为单位密度矩阵，外部仅乘一次密度。

三组刚度参考最大相对误差 {max(r['stiffness_relative_error'] for r in records):.3g}；质量最大相对误差 {max(r['mass_relative_error'] for r in records):.3g}；模态最大残差 {max(r['max_relative_eigen_residual'] for r in records):.3g}。固定梁首频 {frequency_sets[1][0]:.6f} Hz，E 乘 4 后所有频率乘 2，比例最大误差 {scaling:.3g}。

[完整指标](modalsound-fem-metrics.json) · [频率图](../outputs/modalsound_fem/frequencies.png)。矩阵、模态、网格与实际编译二进制保存在 outputs/modalsound_fem。用 `code/run_modalsound_fem.sh` 重跑，Conda pat-tools 提供 Boost 头文件，GCC 9.4 编译，Python 科学计算使用 Linux physgaussian Conda。

这比仅运行球谐基函数进一步验证了真实作者工具中的 FEM；仍不是 PAT 2006 原始场景/测量基准或完整 Qt/FastBEM GUI。与现有 NeuralSound 六面体梁的频率差异不能直接解释为某个实现有错，两种网格的离散精度不同。未运行网格收敛研究。
'''
    (ROOT/'docs/MODALSOUND_FEM.md').write_text(text,encoding='utf-8');print(payload,flush=True)


if __name__=='__main__':main()
