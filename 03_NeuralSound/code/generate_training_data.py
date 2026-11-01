"""Small reproducible procedural dataset for training the actual public networks.

Not ABC or the paper split. Official FEM and boundary topology; local BEM labels
use the released code's acceleration-normalized FFAT convention (no omega^2).
"""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import sys
import json
import time
from pathlib import Path
import numpy as np
from scipy.sparse.linalg import eigsh
from scipy.linalg import solve, eigh

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code/NeuralSound'))
sys.path.insert(0,str(ROOT.parent/'02_PAT/code'))
from src.classic.fem.femModel import Hexahedron_model,Material
from src.classic.bem.util import voxel2boundary,boundary_voxel,boundary_encode,unit_sphere_surface_points
from run_pat_extended import geometry,operator,pressure


def main():
    started=time.perf_counter();rng=np.random.default_rng(20261102)
    out=ROOT/'inputs/procedural_training';out.mkdir(parents=True,exist_ok=True)
    # No pair is merely an axis permutation of another geometry across splits.
    dims=[(a,b,c) for a in (8,10,12,14) for b in (3,4,5) for c in (2,3)]
    order=rng.permutation(len(dims));splits={}
    for split,indices in [('train',order[:16]),('val',order[16:20]),('test',order[20:])]:
        splits[split]=[f'box_{i:02d}.npz' for i in indices]
        (out/f'{split}.txt').write_text('\n'.join(splits[split])+'\n')
    records=[]
    for idx,d in enumerate(dims):
        target=out/f'box_{idx:02d}.npz'
        if target.exists():
            print('EXISTS',target.name,flush=True);continue
        voxel=np.zeros((32,32,32),np.int32)
        lo=(32-np.array(d))//2;hi=lo+d
        voxel[lo[0]:hi[0],lo[1]:hi[1],lo[2]:hi[2]]=1
        coords=np.argwhere(voxel).astype(np.int32)
        model=Hexahedron_model(voxel,Material.Plastic,length=.15)
        K=model.stiff_matrix.tocsc();M=model.mass_matrix.tocsc()
        # Dense reference avoids shift-invert missing vectors in the six-fold
        # rigid eigenspace of these small, symmetric free bodies.
        vals,vecs=eigh(K.toarray(),M.toarray(),subset_by_index=(0,11),driver='gvx')
        order_eig=np.argsort(vals);vals=vals[order_eig];vecs=vecs[:,order_eig]
        assert np.max(np.abs(vals[:6]))<np.min(vals[6:])*1e-6
        vals=vals[6:];vecs=vecs[:,6:]
        residual=np.linalg.norm(K@vecs-(M@vecs)*vals,axis=0)/(np.linalg.norm(K@vecs,axis=0)+np.linalg.norm((M@vecs)*vals,axis=0))
        assert residual.max()<1e-6,(idx,residual)
        vertices=model.vertices
        grid_vertices=np.rint((vertices/.15+.5)*32).astype(int)
        vertex_map={tuple(c):i for i,c in enumerate(grid_vertices)}
        corners=np.array([[0,0,0],[0,0,1],[0,1,0],[0,1,1],[1,0,0],[1,0,1],[1,1,0],[1,1,1]])
        indices=np.array([[vertex_map[tuple(c+p)] for p in corners] for c in coords])
        voxel_modes=vecs.reshape(-1,3,6)[indices].mean(axis=1)
        bv,bf,owner=map(np.asarray,voxel2boundary(coords))
        # Upstream vertex_flag is floating point, so emitted face indices are
        # integral floats; NumPy indexing requires an explicit integer dtype.
        assert np.array_equal(bf,bf.astype(np.int64))
        bf=bf.astype(np.int64);owner=owner.astype(np.int64)
        bv=(bv/32-.5)*.15;mesh=geometry(bv,bf)
        surface,index=map(np.asarray,boundary_voxel(coords))
        code=np.asarray(boundary_encode(surface))
        # As in author's augmentation, sample effective frequencies independently
        # of the unit-box eigenvalues. This is a local shape/frequency dataset.
        freqs=np.geomspace(300,6000,6)*(1+.03*(idx-11.5)/12)
        sphere=unit_sphere_surface_points(32)*.15
        radii=[1.25,1.25**2,1.25**3,3,9,27]
        points=np.concatenate([(sphere*scale).reshape(-1,3) for scale in radii])
        maps=[];far=[]
        for j,freq in enumerate(freqs):
            k=2*np.pi*freq/343
            g=1.225*np.einsum('ij,ij->i',mesh[1],voxel_modes[owner,:,j])
            sigma=solve(operator(mesh,k),g)
            values=(np.abs(pressure(points,mesh,k,sigma))*np.linalg.norm(points,axis=1)).reshape(6,64,32)
            maps.append(values[:3].mean(axis=0));far.append(values[3:].mean(axis=0))
        maps=np.array(maps);far=np.array(far)
        assert np.isfinite(maps).all() and np.all(np.linalg.norm(maps.reshape(6,-1),axis=1)>0)
        np.savez_compressed(target,voxel=voxel,coords=surface,feats_in=voxel_modes[index],
            feats_out=maps,feats_out_far=far,surface=code,freqs=freqs,physical_frequencies=np.sqrt(vals)/(2*np.pi),
            vertices=vertices,modes=vecs,mass_matrix=M.toarray(),stiffness_matrix=K.toarray())
        records.append(dict(file=target.name,dimensions_voxels=list(d),occupied_voxels=len(coords),
            surface_triangles=len(bf),maximum_eigen_residual=float(residual.max())))
        print('GENERATED',records[-1],flush=True)
        (out/'generation-progress.json').write_text(json.dumps(records,indent=2))
    meta=dict(scope='24 procedural cuboids, 144 FFAT maps; not ABC or original paper split',seed=20261102,
        split_by_geometry=splits,label_source='official FEM and voxel boundary; local 7-point indirect BEM',
        convention='released NeuralSound acceleration normalization: neumann=rho*n dot feature, no omega squared',
        records=records,elapsed_s=time.perf_counter()-started)
    (out/'dataset.json').write_text(json.dumps(meta,indent=2))
    (ROOT/'docs/procedural-dataset.json').write_text(json.dumps(meta,indent=2))


if __name__=='__main__':main()
