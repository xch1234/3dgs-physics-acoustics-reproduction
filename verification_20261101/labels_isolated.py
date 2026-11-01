"""Recompute all 144 released Bempp labels using the unchanged local adapter."""
import os,sys,shutil,json
from common import ROOT,AUDIT,save,digest
os.environ['NUMBA_CACHE_DIR']=str(AUDIT/'cache/numba_labels')
sys.path.insert(0,str(ROOT/'03_NeuralSound/code'))
import generate_official_labels as m
import numpy as np
target=AUDIT/'neural_labels'
(target/'docs').mkdir(parents=True,exist_ok=True)
(target/'inputs').mkdir(exist_ok=True)
shutil.copytree(ROOT/'03_NeuralSound/inputs/procedural_training',target/'inputs/procedural_training')
m.ROOT=target
m.main()
rows=[]
for p in sorted((target/'inputs/procedural_bempp').glob('box_*.npz')):
    fresh=np.load(p);old=np.load(ROOT/'03_NeuralSound/inputs/procedural_bempp'/p.name)
    comparisons={}
    for k in ('feats_out','feats_out_far'):
        error=float(np.linalg.norm(fresh[k]-old[k])/np.linalg.norm(old[k]));comparisons[k]=error
        assert error<1e-7,(p,k,error)
    rows.append(dict(file=p.name,relative_differences=comparisons))
assert len(rows)==24
save('checks/fresh-bem-labels.json',dict(passed=True,geometries=24,maps=144,records=rows,adapter_sha256=digest(ROOT/'03_NeuralSound/code/generate_official_labels.py'),scope='Fresh original Bempp operator computation; unchanged local double-precision/Numba/1e-8 adapter; same saved voxel modes, not regenerated FEM or ABC.'))
print('ALL 144 LABELS COMPARED',flush=True)
