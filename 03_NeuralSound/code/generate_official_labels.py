"""Generate all local radiation labels with the released Bempp operators.

Keep the earlier independent collocation labels for comparison. Use CPU Numba,
double precision and audited 1e-8 GMRES for reliable dataset generation.
"""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):
    os.environ[key]='2'
import sys,time,json,shutil
from pathlib import Path
import numpy as np
for key,value in {'bool':bool,'int':int,'float':float,'complex':complex}.items():
    if key not in np.__dict__:setattr(np,key,value)
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'code/NeuralSound'))
import bempp.api as api
import bempp.api.linalg
from bempp.api.operators import boundary,potential
from src.classic.bem import ffat
from src.classic.fem.util import vertex_to_voxel_matrix
from src.classic.bem.util import boundary_voxel


def main():
    source=ROOT/'inputs/procedural_training';out=ROOT/'inputs/procedural_bempp';out.mkdir(parents=True,exist_ok=True)
    original_boundary=ffat.voxel2boundary
    def integer_boundary(*a,**kw):
        v,f,i=original_boundary(*a,**kw)
        return np.asarray(v),np.asarray(f,dtype=np.int64),np.asarray(i,dtype=np.int64)
    ffat.voxel2boundary=integer_boundary
    for module,names in ((boundary.helmholtz,('adjoint_double_layer','hypersingular')),
                         (boundary.sparse,('identity',)),(potential.helmholtz,('single_layer','double_layer'))):
        for name in names:
            original=getattr(module,name)
            def cpu_double(*a,_original=original,**kw):
                kw['device_interface']='numba';kw['precision']='double';return _original(*a,**kw)
            setattr(module,name,cpu_double)
    original_gmres=bempp.api.linalg.gmres;calls=[]
    def checked_gmres(A,b,**kw):
        requested=float(np.real(kw['tol']));kw['tol']=1e-8
        result=original_gmres(A,b,**kw);rhs=b.projections(A.dual_to_range)
        residual=float(np.linalg.norm(A.weak_form()@result[0].coefficients-rhs)/np.linalg.norm(rhs))
        record=dict(info=int(result[1]),iterations=len(result[2]),actual_relative_residual=residual,original_requested_tolerance=requested)
        calls.append(record);print('SOLVE',record,flush=True)
        assert result[1]==0 and residual<1.01e-8,record
        return result
    bempp.api.linalg.gmres=checked_gmres
    records=[];start=time.perf_counter()
    for path in sorted(source.glob('box_*.npz')):
        target=out/path.name;record_path=out/(path.stem+'-solver.json')
        if target.exists() and record_path.exists():
            records.append(json.loads(record_path.read_text()));continue
        d=dict(np.load(path));coords=np.argwhere(d['voxel']);modes=d['modes'].reshape(-1,3,6)
        vib=(vertex_to_voxel_matrix(d['voxel'])@modes.reshape(len(modes),-1)).reshape(len(coords),3,6)
        surface,index=map(np.asarray,boundary_voxel(coords))
        feature_difference=float(np.linalg.norm(vib[index]-d['feats_in'])/np.linalg.norm(d['feats_in']))
        assert np.array_equal(surface,d['coords']) and feature_difference<1e-12
        calls.clear();t=time.perf_counter();print('GENERATING',path.name,flush=True)
        near,far=ffat.vibration_to_ffat(coords,vib,d['freqs'])
        assert len(calls)==6 and np.isfinite(near).all() and np.isfinite(far).all()
        delta=np.linalg.norm((far-d['feats_out_far']).reshape(6,-1),axis=1)/np.linalg.norm(far.reshape(6,-1),axis=1)
        d['feats_out']=near;d['feats_out_far']=far
        np.savez_compressed(target,**d)
        record=dict(file=path.name,seconds=time.perf_counter()-t,gmres=list(calls),
            feature_difference=feature_difference,relative_difference_from_local_far=delta.tolist())
        record_path.write_text(json.dumps(record,indent=2));records.append(record)
        (out/'generation-progress.json').write_text(json.dumps(records,indent=2))
    for phase in ('train','val','test'):shutil.copyfile(source/(phase+'.txt'),out/(phase+'.txt'))
    metadata=dict(scope='24 local cuboids, 144 released Bempp FFAT labels; not ABC',
        complete=len(records)==24,records=records,elapsed_s=time.perf_counter()-start,
        adaptations=['Numba CPU backend instead of crashing POCL','double instead of single operators','GMRES relative tolerance 1e-8 with explicit residual audit','NumPy aliases and integer index compatibility'],
        original_dataset=str(source),geometry_split_unchanged=True)
    assert metadata['complete']
    payload=json.dumps(metadata,indent=2);(out/'dataset.json').write_text(payload)
    (ROOT/'docs/official-labels-dataset.json').write_text(payload)
    print('COMPLETE',metadata['elapsed_s'],flush=True)


if __name__=='__main__':main()
