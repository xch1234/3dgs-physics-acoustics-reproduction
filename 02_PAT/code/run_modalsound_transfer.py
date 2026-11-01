"""Analytic-source validation of original C++ Kirchhoff and multipole pipeline.

Generated FastBEM-format fixtures contain analytic boundary traces, NOT FastBEM
solver output. Air-domain inner boundary normals point into the obstacle.
"""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT.parent/'reproduction/cache/matplotlib'))
import json,hashlib,subprocess
import numpy as np
from scipy.spatial import ConvexHull
from scipy.special import spherical_jn,spherical_yn,sph_harm
from run_pat import refine,sphere_points
import matplotlib.pyplot as plt


def pressure(points,k,sources,weights):
    delta=points[:,None,:]-sources[None,:,:];r=np.linalg.norm(delta,axis=-1)
    G=np.exp(1j*k*r)/(4*np.pi*r)
    p=G@weights
    grad=np.sum((G*(1j*k-1/r)*weights)[...,None]*delta/r[...,None],axis=1)
    return p,grad


def main():
    out=ROOT/'outputs/modalsound_transfer';inputs=ROOT/'inputs/modalsound_transfer';inputs.mkdir(exist_ok=True)
    phi=(1+np.sqrt(5))/2
    vertices=np.array([(0,a,b*phi) for a in (-1,1) for b in (-1,1)]+
        [(a,b*phi,0) for a in (-1,1) for b in (-1,1)]+
        [(b*phi,0,a) for a in (-1,1) for b in (-1,1)],float)
    vertices*=.05/np.linalg.norm(vertices,axis=1)[:,None];faces=ConvexHull(vertices).simplices.copy()
    sources=np.array([[.014,.005,-.009],[-.011,.009,.006],[.004,-.013,.012]])
    strengths=np.array([1.+.2j,-.37+.15j,.21-.31j])
    points=np.r_[sphere_points(120,.13,.27),sphere_points(120,.27,.43)]
    points_file=inputs/'query_points.txt';np.savetxt(points_file,points,fmt='%.17g')
    rows=[];saved={};frequency_values=(400.,1800.,6000.)
    for level in range(3):
        vertices,faces,_=refine(vertices,faces,radius=.05)
        triangles=vertices[faces];center=triangles.mean(axis=1)
        cross=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
        flip=np.einsum('ij,ij->i',cross,center)>0
        faces[flip]=faces[flip][:,[0,2,1]] # inward normal: outer normal of exterior air domain
        triangles=vertices[faces];cross=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
        normals=cross/np.linalg.norm(cross,axis=1)[:,None]
        for frequency in frequency_values:
            k=2*np.pi*frequency/343;rho=1.225
            p,grad=pressure(center,k,sources,strengths)
            normal_velocity=np.einsum('ij,ij->i',grad,normals)/(1j*2*np.pi*frequency*rho)
            tag=f'panels{len(faces)}_hz{int(frequency)}'
            fin=inputs/(tag+'_input.dat');fout=inputs/(tag+'_analytic_trace.dat')
            lines=['Analytic trace fixture; NOT FastBEM solver output','Complete 1/3','Full 0 0.d0',
                f'{len(faces)} {len(vertices)} 0 0','0 0','0','343 1.225','0','0','$ Nodes']
            lines += [f'{i+1} {v[0]:.17g} {v[1]:.17g} {v[2]:.17g}' for i,v in enumerate(vertices)]
            lines+=['$ Elements']
            lines += [f'{i+1} {f[0]+1} {f[1]+1} {f[2]+1} 2 ( {v.real:.17g} , {v.imag:.17g} )' for i,(f,v) in enumerate(zip(faces,normal_velocity))]
            lines+=['$ Field points','END']
            fin.write_text('\n'.join(lines)+'\n')
            lines=[f'Frequency fixture token token token token {frequency:.17g}','Element Pressure']
            lines += [f'{i+1} ( {v.real:.17g} , {v.imag:.17g} )' for i,v in enumerate(p)]
            fout.write_text('\n'.join(lines)+'\n')
            prefix=out/tag
            result=subprocess.run([str(out/'evaluate_transfer'),str(fin),str(fout),str(points_file),str(prefix)],capture_output=True,text=True)
            (out/(tag+'_cpp.log')).write_text(result.stdout+result.stderr)
            if result.returncode:raise RuntimeError(f'C++ evaluator failed: {tag}, {result.returncode}')
            field=np.loadtxt(str(prefix)+'_field.txt');direct=field[:,3]+1j*field[:,4];fast=field[:,5]+1j*field[:,6]
            reference=pressure(points,k,sources,strengths)[0]
            _,order=np.loadtxt(str(prefix)+'_meta.txt',dtype=int)
            moments=np.loadtxt(str(prefix)+'_moments.txt');moments=moments[:,0]+1j*moments[:,1]
            blob=Path(str(prefix)+'_moments.ma').read_bytes()
            assert blob[:4]==b'MA\x09\x12',blob[:4]
            dims=np.frombuffer(blob,dtype='<i4',count=3,offset=4)
            assert list(dims)==[2,order*order,2],dims
            binary=np.frombuffer(blob,dtype='<f8',offset=16).reshape(2,order*order).T
            np.testing.assert_array_equal(binary[:,0]+1j*binary[:,1],moments)
            # Independent SciPy evaluator verifies stored moments/conventions.
            radii=np.linalg.norm(points,axis=1);theta=np.arccos(points[:,2]/radii);az=np.arctan2(points[:,1],points[:,0])
            python=np.zeros(len(points),complex);idx=0
            for n in range(order):
                for m in range(-n,n+1):
                    Y=sph_harm(m,n,az,theta)*((-1.)**m if m>0 else 1.)
                    python+=moments[idx]*(spherical_jn(n,k*radii)+1j*spherical_yn(n,k*radii))*Y;idx+=1
            python*=1j*k
            rel=lambda a,b:float(np.linalg.norm(a-b)/np.linalg.norm(b))
            row=dict(panels=len(faces),frequency_Hz=frequency,expansion_order_count=int(order),query_points=len(points),
                direct_vs_analytic_relative_L2=rel(direct,reference),multipole_vs_direct_relative_L2=rel(fast,direct),
                multipole_vs_analytic_relative_L2=rel(fast,reference),saved_moments_scipy_relative_L2=rel(python,fast),binary_moments_roundtrip_exact=True)
            assert np.isfinite(field).all() and np.isfinite(moments).all(),tag
            assert row['multipole_vs_direct_relative_L2']<1e-6,row
            assert row['saved_moments_scipy_relative_L2']<1e-10,row
            rows.append(row);saved[tag]=np.c_[reference,direct,fast,python]
            print(row,flush=True)
    for freq in frequency_values:
        selected=[r for r in rows if r['frequency_Hz']==freq]
        errors=[r['direct_vs_analytic_relative_L2'] for r in selected]
        assert all(a>b for a,b in zip(errors,errors[1:])),(freq,errors)
        assert errors[-1]<.03,(freq,errors)
    np.savez_compressed(out/'reference_arrays.npz',query_points=points,sources=sources,strengths=strengths,**saved)
    source_files=['transfer/BoundaryIntegralTransfer.hpp','transfer/FMMBoundIntTransfer.hpp','transfer/HelmholtzBasis.hpp']
    checks=dict(all_checks_passed=True,records=rows,source_sha256={p:hashlib.sha256((ROOT/'code/ModalSound/ModalSound/src'/p).read_bytes()).hexdigest() for p in source_files},
        scope='actual original C++ boundary integral, multipole moments, binary moment export and evaluation; analytic traces, not a FastBEM solve or PAT adaptive source placement',
        convention='e^(-i omega t), G=e^(i k r)/(4 pi r); normals into solid (outward normals of exterior air domain); dp/dn=i omega rho v')
    payload=json.dumps(checks,indent=2);(out/'metrics.json').write_text(payload);(ROOT/'docs/modalsound-transfer-metrics.json').write_text(payload)
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
    for f in frequency_values:
        selected=[r for r in rows if r['frequency_Hz']==f]
        ax.loglog([r['panels'] for r in selected],[r['direct_vs_analytic_relative_L2'] for r in selected],'o-',label=f'{f:g} Hz')
    ax.set(xlabel='Boundary triangles',ylabel='Relative complex-pressure L2 error',title='Original C++ integration vs exact interior sources');ax.legend()
    fig.savefig(out/'convergence.png',dpi=160);plt.close(fig)
    text='\n'.join(f'- {r["frequency_Hz"]:g} Hz、{r["panels"]} 面片：原积分/解析误差 {r["direct_vs_analytic_relative_L2"]:.6g}，多极子/原积分 {r["multipole_vs_direct_relative_L2"]:.3g}。' for r in rows)
    report=f'''# 原 ModalSound 边界积分与多极子后处理

本次实际编译运行 BoundaryIntegralTransfer、FMMBoundIntTransfer::compute_moments/eval/store_moments。使用三个非对称复单极点声源的解析声压与梯度，生成明确标记的 FastBEM 格式测试输入。它们不是 FastBEM 求解器输出，也没有取得该外部求解器。未修改上游头文件。

80/320/1280 面片，400/1800/6000 Hz，每例 240 个独立外部查询点；保留原代码自选展开阶数、文本及二进制矩系数。边界法向指向物体内部（外部空气域的外法向）；采用 e^(-iωt)、第一类 Hankel，不能与本地 PAT 的相反相位约定直接混用。

{text}

各频率的解析误差随加密下降，最细网格低于 3%；多极子求值与相同离散积分相符，独立 SciPy 对保存系数的复算也通过。这里只验证后处理，不把多极子与积分接近当作连续声场同等准确，更不是 PAT 2006 自适应 source placement 的原始实现。

[指标](modalsound-transfer-metrics.json) · [收敛图](../outputs/modalsound_transfer/convergence.png) · [参考数组](../outputs/modalsound_transfer/reference_arrays.npz)。重跑 code/run_modalsound_transfer.sh；使用已有 Conda GSL/Boost 与项目内固定 Eigen 3.3.7 头文件，下载来源和 SHA256 见 code/dependencies/eigen-provenance.json。没有安装 Qt、没有变更系统或项目外配置。
'''
    (ROOT/'docs/MODALSOUND_TRANSFER.md').write_text(report,encoding='utf-8')


if __name__=='__main__':main()
