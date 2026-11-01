"""Run released Bempp FFAT on a saved local sample, auditing GMRES.

The default retains the author's tolerance, arithmetic and operators. A separate
--tolerance run may set a practical single-precision GMRES tolerance explicitly.
"""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','POCL_MAX_PTHREAD_COUNT','NUMBA_NUM_THREADS'):
    os.environ[key]='2'
import sys,json,time,argparse
from pathlib import Path
import numpy as np
# Bempp-cl 0.2.4 predates NumPy 1.24's removal of builtin aliases.
for _name,_type in {'bool':bool,'int':int,'float':float,'complex':complex}.items():
    if _name not in np.__dict__:setattr(np,_name,_type)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code/NeuralSound'))
import bempp.api as api
import bempp.api.linalg
from src.classic.bem import ffat
from src.classic.fem.util import vertex_to_voxel_matrix


def main():
    p=argparse.ArgumentParser();p.add_argument('--sample',default='box_00.npz')
    p.add_argument('--tolerance',type=float)
    p.add_argument('--backend',choices=['opencl','numba'],default='opencl')
    p.add_argument('--precision',choices=['single','double'],default='single');args=p.parse_args()
    tag='official_bem' if args.tolerance is None else 'official_bem_practical_tolerance'
    if args.backend!='opencl':tag+='_'+args.backend
    if args.precision!='single':tag+='_'+args.precision
    out=ROOT/'outputs'/tag;out.mkdir(parents=True,exist_ok=True)
    d=dict(np.load(ROOT/'inputs/procedural_training'/args.sample))
    coords=np.argwhere(d['voxel']);modes=d['modes'].reshape(-1,3,6)
    vib=(vertex_to_voxel_matrix(d['voxel'])@modes.reshape(len(modes),-1)).reshape(len(coords),3,6)
    # Released voxel2boundary uses a float vertex lookup table, emitting integral
    # float indices. Convert only the indexing arrays, not the geometry.
    original_boundary=ffat.voxel2boundary
    def integer_boundary(*a,**kw):
        v,f,i=original_boundary(*a,**kw)
        return np.asarray(v),np.asarray(f,dtype=np.int64),np.asarray(i,dtype=np.int64)
    ffat.voxel2boundary=integer_boundary
    api.BOUNDARY_OPERATOR_DEVICE_TYPE='cpu';api.POTENTIAL_OPERATOR_DEVICE_TYPE='cpu'
    if args.backend=='numba' or args.precision!='single':
        # Same Bempp Galerkin operators, supported alternative kernel backend.
        from bempp.api.operators import boundary,potential
        for module,names in ((boundary.helmholtz,('adjoint_double_layer','hypersingular')),
                             (boundary.sparse,('identity',)),
                             (potential.helmholtz,('single_layer','double_layer'))):
            for name in names:
                original=getattr(module,name)
                def use_numba(*a,_original=original,**kw):
                    kw['device_interface']=args.backend;kw['precision']=args.precision
                    return _original(*a,**kw)
                setattr(module,name,use_numba)
    calls=[];original_gmres=bempp.api.linalg.gmres
    def audited_gmres(*a,**kw):
        requested=kw.get('tol')
        if args.tolerance is not None:kw['tol']=args.tolerance
        start=time.perf_counter();result=original_gmres(*a,**kw)
        A,b=a[:2];rhs=b.projections(A.dual_to_range)
        actual_residual=float(np.linalg.norm(A.weak_form()@result[0].coefficients-rhs)/np.linalg.norm(rhs))
        row=dict(info=int(result[1]),iterations=len(result[2]),seconds=time.perf_counter()-start,
                 independently_recomputed_relative_residual=actual_residual,
                 requested_tolerance=float(np.real(requested)),used_tolerance=float(np.real(kw['tol'])),
                 final_reported_residual=float(result[2][-1]) if len(result[2]) else None)
        calls.append(row);print('GMRES',row,flush=True)
        (out/'solver-progress.json').write_text(json.dumps(calls,indent=2))
        return result
    bempp.api.linalg.gmres=audited_gmres
    start=time.perf_counter()
    near,far=ffat.vibration_to_ffat(coords,vib,d['freqs'],showTimeStatistics=True)
    assert np.isfinite(near).all() and np.isfinite(far).all()
    errors_near=np.linalg.norm((near-d['feats_out']).reshape(6,-1),axis=1)/np.linalg.norm(near.reshape(6,-1),axis=1)
    errors_far=np.linalg.norm((far-d['feats_out_far']).reshape(6,-1),axis=1)/np.linalg.norm(far.reshape(6,-1),axis=1)
    np.savez_compressed(out/'ffat_comparison.npz',official_near=near,official_far=far,
                        local_near=d['feats_out'],local_far=d['feats_out_far'],frequencies=d['freqs'])
    metrics=dict(scope='released hypersingular Bempp FFAT vs local indirect collocation BEM on identical cuboid',
        sample=args.sample,all_outputs_finite=True,all_gmres_converged=all(r['info']==0 for r in calls),
        relative_map_difference_near=errors_near.tolist(),relative_map_difference_far=errors_far.tolist(),
        gmres=calls,elapsed_s=time.perf_counter()-start,
        adaptations=[f'CPU {args.backend} backend',f'{args.precision} precision operators','integral index dtype adapter','NumPy removed builtin aliases restored for Bempp 0.2.4']+([] if args.tolerance is None else [f'GMRES tolerance={args.tolerance}']))
    payload=json.dumps(metrics,indent=2);(out/'metrics.json').write_text(payload)
    (ROOT/'docs'/f'{tag}-metrics.json').write_text(payload)
    fig,axs=plt.subplots(3,2,figsize=(9,8),layout='constrained')
    for row,j in enumerate((0,2,5)):
        for col,a in enumerate((far[j],d['feats_out_far'][j])):
            axs[row,col].imshow(a.T,origin='lower',vmin=0,vmax=max(far[j].max(),d['feats_out_far'][j].max()))
            axs[row,col].set_title(f'{d["freqs"][j]:.0f} Hz / '+('released Bempp' if col==0 else 'local BEM'))
    fig.savefig(out/'map_comparison.png',dpi=150);plt.close(fig)
    print(payload,flush=True)


if __name__=='__main__':main()
