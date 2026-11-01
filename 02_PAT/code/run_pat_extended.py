"""PAT 2006 distance-field offset and randomized multilevel placement.

Extends the recorded small-beam reproduction, not the original paper scenes.
Uses degree-five triangle quadrature and all twelve available FEM modes.
"""
import run_pat as base  # also fixes numerical-library thread counts
import json
import time
from pathlib import Path
import numpy as np
import mcubes
import matplotlib.pyplot as plt
from scipy.linalg import solve, svd, lstsq
from scipy.special import sph_harm
from scipy.spatial import ConvexHull
from scipy.io import wavfile

OUT = base.ROOT / 'outputs' / 'pat_extended'
BARY = np.array([[1/3]*3, [.059715871789770,.470142064105115,.470142064105115],
    [.470142064105115,.059715871789770,.470142064105115], [.470142064105115,.470142064105115,.059715871789770],
    [.797426985353087,.101286507323456,.101286507323456], [.101286507323456,.797426985353087,.101286507323456],
    [.101286507323456,.101286507323456,.797426985353087]])
QWEIGHT = np.array([.225]+[.132394152788506]*3+[.125939180544827]*3)


def geometry(v, f):
    center, normal, area, _ = base.panels(v, f)
    return center, normal, area, np.einsum('qv,pvd->pqd', BARY, v[f])


def operator(mesh, k):
    center, normal, area, quad = mesh
    n = len(area)
    A = np.empty((n, n), complex)
    for start in range(0, n, 64):
        stop = min(start+64, n)
        rows = np.arange(stop-start); cols = np.arange(start, stop)
        block = np.zeros((stop-start, n), complex)
        for q, weight in enumerate(QWEIGHT):
            delta = center[start:stop,None]-quad[None,:,q]
            r = np.linalg.norm(delta, axis=2); r[rows,cols] = 1
            dot = np.einsum('ijd,id->ij', delta, normal[start:stop])
            kernel = np.exp(-1j*k*r)*(-1j*k*r-1)*dot/(4*np.pi*r**3)
            kernel[rows,cols] = 0
            block += kernel*area*weight
        block[rows,cols] -= .5
        A[start:stop] = block
    return A


def pressure(points, mesh, k, density):
    _, _, area, quad = mesh
    result = []
    for start in range(0, len(points), 128):
        block = points[start:start+128]
        G = np.zeros((len(block),len(area)),complex)
        for q, weight in enumerate(QWEIGHT):
            r = np.linalg.norm(block[:,None]-quad[None,:,q],axis=2)
            G += np.exp(-1j*k*r)/(4*np.pi*r)*area*weight
        result.append(G@density)
    return np.concatenate(result)


def basis(points, source, k, order=3):
    d = points-source
    r = np.linalg.norm(d,axis=1)
    az = np.arctan2(d[:,1],d[:,0]); polar = np.arccos(np.clip(d[:,2]/r,-1,1))
    return np.column_stack([base.hankel(l,k*r)*sph_harm(m,l,az,polar)
                            for l in range(order) for m in range(-l,l+1)])


def multi_fit(points, target, areas, k, levels=3, seed=20261101, max_sources=32):
    started = time.perf_counter()
    rng = np.random.default_rng(seed)
    weights = np.sqrt(areas); b = target*weights
    residual = b.copy(); matrices=[]; centers=[]; history=[1.]
    alpha=.25; candidates_per_round=128; evaluations=0
    for _ in range(max_sources):
        candidates=rng.uniform([-.058,-.018,-.018],[.058,.018,.018],(candidates_per_round,3))
        probability=.5*areas/areas.sum()+.5*np.abs(residual)**2/np.linalg.norm(residual)**2
        for level in range(1, levels+1):
            count=max(18,int(np.ceil(len(points)*alpha**(levels-level))))
            selected=(rng.choice(len(points),count,replace=False,p=probability)
                      if level<levels else np.arange(len(points)))
            scores=[]
            for c in candidates:
                M=basis(points[selected],c,k)*weights[selected,None]
                U,s,_=svd(M,full_matrices=False)
                U=U[:,s>s[0]*1e-6]
                scores.append(np.linalg.norm(U.conj().T@residual[selected])**2)
                evaluations+=len(selected)
            keep=max(1,int(np.ceil(candidates_per_round*alpha**level))) if level<levels else 1
            candidates=candidates[np.argsort(scores)[-keep:]]
        center=candidates[-1]; centers.append(center)
        matrices.append(basis(points,center,k)*weights[:,None])
        A=np.concatenate(matrices,axis=1)
        coeff,_,rank,_=lstsq(A,b,cond=1e-6,lapack_driver='gelsd')
        residual=b-A@coeff
        history.append(float(np.linalg.norm(residual)/np.linalg.norm(b)))
        if history[-1]<.02: break
    return np.array(centers),coeff,dict(levels=levels,alpha=alpha,random_candidates_per_round=candidates_per_round,
        source_count=len(centers),coefficients=len(coeff),fit_relative_L2=history[-1],history=history,
        evaluated_sample_candidate_pairs=evaluations,svd_rank=int(rank),fit_seconds=time.perf_counter()-started)


def evaluate(points, centers, coeff, k):
    return np.concatenate([basis(points,c,k) for c in centers],axis=1)@coeff


def offset_surface():
    h=.005; delta=.02
    lower=np.array([-.09,-.05,-.05]); upper=-lower
    axes=[np.arange(a,b+h*.5,h) for a,b in zip(lower,upper)]
    xyz=np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1)
    q=np.abs(xyz)-np.array([.06,.02,.02])
    signed=np.linalg.norm(np.maximum(q,0),axis=-1)+np.minimum(q.max(axis=-1),0)
    v,f=mcubes.marching_cubes(signed,delta)
    v=v*h+lower
    mesh=geometry(v,f)
    np.savez_compressed(OUT/'offset_mesh.npz',vertices=v,triangles=f,centroids=mesh[0],areas=mesh[2],spacing=h,offset=delta)
    return mesh[0],mesh[2]


def analytic_validation():
    gold=(1+np.sqrt(5))/2; radius=.05
    v=np.array([(0,a,b*gold) for a in (-1,1) for b in (-1,1)]+
               [(a,b*gold,0) for a in (-1,1) for b in (-1,1)]+
               [(b*gold,0,a) for a in (-1,1) for b in (-1,1)],float)
    v*=radius/np.linalg.norm(v[0]); f=ConvexHull(v).simplices
    query=base.sphere_points(180,.3); results=[]
    for level in range(3):
        v,f,_=base.refine(v,f,radius=radius); mesh=geometry(v,f)
        for l,frequency in ((0,400),(1,1800)):
            k=2*np.pi*frequency/343
            c=mesh[0]; r=np.linalg.norm(c,axis=1)
            g=sph_harm(0,l,np.arctan2(c[:,1],c[:,0]),np.arccos(c[:,2]/r))
            sigma=solve(operator(mesh,k),g)
            ref=base.hankel(l,k*.3)/(k*base.hankel(l,k*radius,True))*sph_harm(
                0,l,np.arctan2(query[:,1],query[:,0]),np.arccos(query[:,2]/.3))
            error=float(np.linalg.norm(pressure(query,mesh,k,sigma)-ref)/np.linalg.norm(ref))
            results.append(dict(panels=len(f),harmonic_l=l,frequency_Hz=frequency,error=error))
            print('sphere',results[-1],flush=True)
    assert all(r['error']<.05 for r in results[-2:]),results
    return results


def main():
    started=time.perf_counter(); OUT.mkdir(parents=True,exist_ok=True)
    analytic=analytic_validation()
    data=dict(np.load(base.FEM)); v,f,m1=base.beam_surface(data)
    other=dict(data); other['clamped_modes_mass_normalized']=other['clamped_modes_mass_normalized'][:,6:]
    _,_,m2=base.beam_surface(other); modes=np.concatenate((m1,m2),axis=2)
    coarse_v,coarse_f,coarse_m=base.refine(v,f,modes)
    v,f,modes=base.refine(coarse_v,coarse_f,coarse_m)
    mesh=geometry(v,f); offset,areas=offset_surface()
    validation=np.r_[base.sphere_points(240,.12,.71),base.sphere_points(240,.3,1.83)]
    frequencies=data['frequencies_Hz']; listeners=np.array([[.3,0,0],[0,.3,0],[0,0,.3]])
    transfer_bem=np.zeros((3,12),complex); transfer_pat=transfer_bem.copy()
    results=[]; comparisons=[]
    for j,freq in enumerate(frequencies):
        w=2*np.pi*freq; k=w/343
        g=1.225*w*w*np.einsum('ij,ij->i',modes[f,:,j].mean(axis=1),mesh[1])
        sigma=solve(operator(mesh,k),g)
        target=pressure(offset,mesh,k,sigma)
        centers,coeff,stats=multi_fit(offset,target,areas,k,seed=20261101+j)
        ref=pressure(validation,mesh,k,sigma); approx=evaluate(validation,centers,coeff,k)
        error=float(np.linalg.norm(approx-ref)/np.linalg.norm(ref))
        stats.update(mode=j+1,frequency_Hz=float(freq),heldout_relative_L2=error)
        results.append(stats)
        transfer_bem[:,j]=pressure(listeners,mesh,k,sigma)
        transfer_pat[:,j]=evaluate(listeners,centers,coeff,k)
        np.savez_compressed(OUT/f'mode_{j+1:02d}.npz',centers=centers,coefficients=coeff,
            validation_points=validation,bem_pressure=ref,pat_pressure=approx,offset_pressure=target,density=sigma)
        print('mode',j+1,'fit',stats['fit_relative_L2'],'heldout',error,'sources',len(centers),flush=True)
        if j in (0,5,11):
            cm=geometry(coarse_v,coarse_f)
            gc=1.225*w*w*np.einsum('ij,ij->i',coarse_m[coarse_f,:,j].mean(axis=1),cm[1])
            pc=pressure(validation,cm,k,solve(operator(cm,k),gc))
            _,_,single=multi_fit(offset,target,areas,k,levels=1,seed=20261101+j)
            comparisons.append(dict(mode=j+1,bem_448_vs_1792=float(np.linalg.norm(pc-ref)/np.linalg.norm(ref)),
                single_level=single,multilevel=stats,observed_fit_speed_ratio=single['fit_seconds']/stats['fit_seconds']))
        (OUT/'progress.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    fs=48000;t=np.arange(fs*3)/fs
    vertices=data['vertices_m'];hit=int(np.argmax(vertices@np.array([1,.1,.01])))
    full=np.zeros((len(vertices)*3,12));full[data['free_dofs']]=data['clamped_modes_mass_normalized']
    impulse=full.reshape(-1,3,12)[hit,1]*.001
    w=2*np.pi*frequencies;d=(30+1e-6*w*w)/2;wd=np.sqrt(w*w-d*d)
    q=impulse[:,None]/wd[:,None]*np.exp(-d[:,None]*t)*np.sin(wd[:,None]*t)
    b=np.abs(transfer_bem)@q;p=np.abs(transfer_pat)@q
    gain=.85/max(np.abs(b).max(),np.abs(p).max());fade=np.ones(len(t));fade[-960:]=np.linspace(1,0,960)
    for name,signals in [('bem',b),('pat',p)]:
        for i,axis in enumerate('xyz'):
            wave=np.rint(signals[i]*gain*fade*32767).astype(np.int16)
            wavfile.write(OUT/f'{name}_{axis}.wav',fs,wave)
    np.savez_compressed(OUT/'audio_raw.npz',time_s=t,bem_pressure_Pa=b,pat_pressure_Pa=p,common_gain=gain)
    np.savez_compressed(OUT/'beam_mesh.npz',vertices=v,triangles=f,modes=modes)
    passed=all(r['heldout_relative_L2']<.08 and r['fit_relative_L2']<.05 for r in results)
    metrics=dict(scope='PAT small-beam method reproduction extended through section 4.3.2',all_checks_passed=passed,
        panels=len(f),modes=12,offset_samples=len(offset),offset_distance_m=.02,offset_grid_spacing_m=.005,
        multipole_order=3,terms_per_center=9,quadrature='7-point degree-five Dunavant',
        analytic_sphere_validation=analytic,mode_results=results,comparisons=comparisons,
        audio_relative_L2=float(np.linalg.norm(p-b)/np.linalg.norm(b)),elapsed_s=time.perf_counter()-started)
    text=json.dumps(metrics,indent=2)
    (OUT/'metrics.json').write_text(text,encoding='utf-8')
    (base.ROOT/'docs/extended-metrics.json').write_text(text,encoding='utf-8')
    fig,ax=plt.subplots(1,3,figsize=(14,4),layout='constrained')
    for l in (0,1):
        vals=[r for r in analytic if r['harmonic_l']==l]
        ax[0].loglog([r['panels'] for r in vals],[r['error'] for r in vals],'o-',label=f'l={l}')
    ax[0].legend();ax[0].set(title='Analytic sphere reference',xlabel='Panels',ylabel='Relative complex error')
    ax[1].bar(np.arange(1,13),[r['heldout_relative_L2']*100 for r in results]);ax[1].set(title='Held-out PAT vs BEM',xlabel='Mode',ylabel='Error (%)')
    ax[2].bar([str(r['mode']) for r in comparisons],[r['observed_fit_speed_ratio'] for r in comparisons]);ax[2].set(title='Observed fitting speed ratio',xlabel='Mode',ylabel='Single / multilevel wall time')
    fig.savefig(OUT/'validation.png',dpi=160);plt.close(fig)
    print(text,flush=True)
    assert passed,'Extended fit thresholds not met; inspect saved metrics, do not label success.'


if __name__=='__main__': main()
