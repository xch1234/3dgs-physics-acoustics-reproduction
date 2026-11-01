"""Reassemble physical FEM on CPU and verify saved neural refinement vectors."""
import os,sys,json,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
os.environ['NUMBA_NUM_THREADS']='1';os.environ['NUMBA_CACHE_DIR']=str(ROOT/'reproduction/cache/numba')
sys.dont_write_bytecode=True
import numpy as np
from scipy.linalg import eigh
sys.path.insert(0,str(ROOT/'03_NeuralSound/code/NeuralSound'))
from src.classic.fem.femModel import Hexahedron_model,Material


def main():
    p=argparse.ArgumentParser();p.add_argument('--paper-schedule',action='store_true');args=p.parse_args()
    tag='vibration_paper_schedule' if args.paper_schedule else 'vibration_training'
    folder=ROOT/'03_NeuralSound/outputs'/tag
    metrics=json.loads((folder/'metrics.json').read_text());records=[];models={}
    for row in metrics['refinement']:
        name=row['sample'];method=row['initialization']
        if name not in models:
            with np.load(ROOT/'03_NeuralSound/inputs/procedural_training'/name) as data:voxel=data['voxel']
            physical=Hexahedron_model(voxel,Material.Ceramic)
            K=physical.stiff_matrix.toarray();M=physical.mass_matrix.toarray()
            reference=eigh(K,M,subset_by_index=(0,19),eigvals_only=True)
            models[name]=(K,M,reference)
        K,M,reference=models[name]
        with np.load(folder/f'{Path(name).stem}_{method}.npz') as a:
            U=a['modes'];assert np.isfinite(U).all() and U.shape==(len(K),20)
            assert np.isfinite(a['eigenvalues']).all()
        elastic=U[:,6:20];KU=K@elastic;MU=M@elastic
        rayleigh=np.sum(elastic*KU,axis=0)/np.sum(elastic*MU,axis=0)
        residual=np.linalg.norm(KU-MU*rayleigh,axis=0)/(np.linalg.norm(KU,axis=0)+np.linalg.norm(MU*rayleigh,axis=0))
        eigen_error=np.max(np.abs(rayleigh/reference[6:20]-1))
        gram=U.T@M@U;factor=np.diag(gram).mean();orth_error=np.max(np.abs(gram/factor-np.eye(20)))
        assert residual.max()<1e-6 and eigen_error<1e-6 and orth_error<1e-6,(name,method,residual.max(),eigen_error,orth_error)
        records.append(dict(sample=name,initialization=method,elastic_per_mode_max_residual=float(residual.max()),
            elastic_eigenvalue_max_relative_error=float(eigen_error),scaled_mass_orthogonality_error=float(orth_error)))
    assert len(records)==12
    report=dict(passed=True,records=records,scope='CPU reassembled Ceramic FEM, physical Rayleigh quotients, all 14 saved elastic vectors and all 20-vector mass orthogonality; no network rerun')
    filename='paper-schedule-vibration-array-audit.json' if args.paper_schedule else 'vibration-array-audit.json'
    (ROOT/'03_NeuralSound/docs'/filename).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
