"""Released example OBJ -> CUDA voxelizer -> official FEM and GPU LOBPCG.

Also computes an independent sparse double-precision reference, preserving the
released solver's actual residuals instead of assuming convergence.
"""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='2'
import sys,time,json,hashlib,argparse
from pathlib import Path
import numpy as np
import torch
from scipy.sparse.linalg import eigsh
from scipy.sparse import save_npz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT/'code/NeuralSound';sys.path.insert(0,str(REPO))
from src.classic.tools import voxelize_mesh
from src.classic.fem.femModel import Hexahedron_model,Material
from src.classic.fem.solver import LOBPCG_solver


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--voxel-only',action='store_true')
    parser.add_argument('--reuse-voxel',action='store_true');args=parser.parse_args()
    torch.manual_seed(20261102);np.random.seed(20261102);torch.set_num_threads(2)
    out=ROOT/'outputs/official_example';out.mkdir(parents=True,exist_ok=True)
    source=REPO/'dataset/mesh/example.obj';start=time.perf_counter()
    voxel=np.load(out/'voxel.npy') if args.reuse_voxel else voxelize_mesh(str(source))
    np.save(out/'voxel.npy',voxel)
    print('VOXEL',voxel.shape,int(voxel.sum()),flush=True)
    if args.voxel_only:return
    model=Hexahedron_model(voxel,Material.Ceramic)
    K=model.stiff_matrix.tocsc();M=model.mass_matrix.tocsc()
    print('FEM',K.shape,K.nnz,flush=True)
    save_npz(out/'stiffness.npz',K);save_npz(out/'mass.npz',M)
    t=time.perf_counter()
    E,U=LOBPCG_solver(k=20)(K.tocoo(),M.tocoo())
    elapsed_official=time.perf_counter()-t
    residual=np.linalg.norm(K@U-(M@U)*E,axis=0)/(np.linalg.norm(K@U,axis=0)+np.linalg.norm((M@U)*E,axis=0))
    np.savez_compressed(out/'official_modes.npz',eigenvalues=E,modes=U,residuals=residual)
    print('OFFICIAL',elapsed_official,residual.tolist(),flush=True)
    t=time.perf_counter()
    Er,Ur=eigsh(K,k=26,M=M,sigma=-1e5,which='LM',tol=1e-10,maxiter=10000)
    order=np.argsort(Er);Er=Er[order];Ur=Ur[:,order]
    assert np.max(np.abs(Er[:6]))<Er[6]*1e-6
    Er=Er[6:];Ur=Ur[:,6:]
    rr=np.linalg.norm(K@Ur-(M@Ur)*Er,axis=0)/(np.linalg.norm(K@Ur,axis=0)+np.linalg.norm((M@Ur)*Er,axis=0))
    assert rr.max()<1e-6,rr
    np.savez_compressed(out/'reference_modes.npz',eigenvalues=Er,modes=Ur,residuals=rr,vertices=model.vertices)
    metrics=dict(scope='author example mesh, unmodified CUDA voxelizer/FEM/GPU LOBPCG; independent reference audit',
        source=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),occupied_voxels=int(voxel.sum()),
        degrees_of_freedom=K.shape[0],official_seconds=elapsed_official,reference_seconds=time.perf_counter()-t,
        official_relative_residuals=residual.tolist(),reference_relative_residuals=rr.tolist(),
        official_frequencies_hz=(np.sqrt(np.maximum(E,0))/(2*np.pi)).tolist(),reference_frequencies_hz=(np.sqrt(Er)/(2*np.pi)).tolist(),
        eigenvalue_relative_errors=(np.abs(E-Er)/Er).tolist(),elapsed_s=time.perf_counter()-start)
    payload=json.dumps(metrics,indent=2);(out/'metrics.json').write_text(payload)
    (ROOT/'docs/official-example-metrics.json').write_text(payload)
    fig=plt.figure(figsize=(10,4),layout='constrained');ax=fig.add_subplot(121,projection='3d')
    ax.voxels(voxel,edgecolor=None,facecolors='#3b82b6');ax.set_title('Official CUDA voxelization / 32 cubed')
    ax=fig.add_subplot(122);ax.plot(np.sqrt(Er)/(2*np.pi),'o-',label='double sparse reference')
    ax.plot(np.sqrt(np.maximum(E,0))/(2*np.pi),'x',label='released GPU LOBPCG');ax.set(xlabel='Elastic mode',ylabel='Frequency (Hz)');ax.legend()
    fig.savefig(out/'example_validation.png',dpi=150);plt.close(fig)
    print(payload,flush=True)


if __name__=='__main__':main()
