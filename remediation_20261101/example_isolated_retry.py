"""Replay voxelization and full example solve without mixed CUDA contexts."""
import sys,json
from common import ROOT,AUDIT,save
import numpy as np
root=AUDIT/'neural_example_retry';out=root/'outputs/official_example'
for folder in [out,root/'docs']:folder.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'03_NeuralSound/code'))
sys.path.insert(0,str(ROOT/'03_NeuralSound/code/NeuralSound'))
task=sys.argv[1]
if task=='voxel':
 from src.classic.tools import voxelize_mesh
 voxel=voxelize_mesh(str(ROOT/'03_NeuralSound/code/NeuralSound/dataset/mesh/example.obj'))
 np.testing.assert_array_equal(voxel,np.load(AUDIT/'neural_extensions/outputs/official_example/voxel.npy'))
 np.save(out/'voxel.npy',voxel);print('Independent PyCUDA process:',voxel.shape,int(voxel.sum()),flush=True)
elif task=='solve':
 import run_official_example as m
 m.ROOT=root;sys.argv=[sys.argv[0],'--reuse-voxel'];m.main()
 assert 'pycuda.autoinit' not in sys.modules,'Solve must not create a PyCUDA context'
 print('Full Torch solve finished without importing pycuda.autoinit; normal exit follows.',flush=True)
elif task=='compare':
 from scipy.sparse import load_npz
 first=AUDIT/'neural_extensions/outputs/official_example'
 for name in ['stiffness.npz','mass.npz']:
  old=load_npz(first/name);new=load_npz(out/name)
  assert old.shape==new.shape and (old-new).nnz==0,name
 a=dict(np.load(first/'reference_modes.npz'));b=dict(np.load(out/'reference_modes.npz'))
 np.testing.assert_allclose(a['eigenvalues'],b['eigenvalues'],rtol=1e-8,atol=1e-3)
 assert max(a['residuals'].max(),b['residuals'].max())<1e-6
 save('checks/V28-example-retry-numerics.json',dict(passed=True,voxel_array_equal=True,mass_and_stiffness_exactly_equal=True,reference_eigenvalues_relative_difference=float(np.max(np.abs(a['eigenvalues']-b['eigenvalues'])/b['eigenvalues'])),original_reference_max_residual=float(a['residuals'].max()),retry_reference_max_residual=float(b['residuals'].max()),scope='First-run artifacts retained and used downstream; exact FEM matrices and independent reference checks confirm those data. Complete replay uses separate CUDA processes and must also exit normally.'))
 print('Original and replay FEM matrices/reference verified.',flush=True)
else:raise ValueError(task)
