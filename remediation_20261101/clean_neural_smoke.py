"""Exercise fresh CUDA libraries in separate, normally exiting processes."""
import sys,json
from common import ROOT,AUDIT,save,run,runtime_env
if len(sys.argv)==1:
 rows=[]
 for task in ['voxel','scatter']:
  rows.append(run('V30-clean-neural-'+task+'-isolated',[sys.executable,'-X','faulthandler','-u',__file__,task],env=runtime_env(sys.prefix),required=False))
 ok=all(r['exit_code']==0 for r in rows)
 payload=dict(passed=ok,commands=rows,scope='PyCUDA voxelizer and torch-scatter in distinct normally exiting processes, avoiding mixed CUDA context teardown. Same fresh Conda prefix; AcousticNet separately checked.')
 if ok:
  payload.update(json.loads((AUDIT/'checks/V30-clean-neural-voxel-isolated.json').read_text()));payload['scatter_result']=json.loads((AUDIT/'checks/V30-clean-neural-scatter-isolated.json').read_text())['scatter_result']
 save('checks/V30-clean-neural-kernels.json',payload)
 if not ok:raise SystemExit(1)
elif sys.argv[1]=='voxel':
 import numpy as np
 sys.path.insert(0,str(ROOT/'03_NeuralSound/code/NeuralSound'))
 from src.classic.tools import voxelize_mesh
 source=ROOT/'03_NeuralSound/code/NeuralSound/dataset/mesh/example.obj'
 voxel=voxelize_mesh(str(source));ref=np.load(AUDIT/'neural_extensions/outputs/official_example/voxel.npy');np.testing.assert_array_equal(voxel,ref)
 (AUDIT/'neural_clean').mkdir(exist_ok=True);np.save(AUDIT/'neural_clean/voxel.npy',voxel)
 save('checks/V30-clean-neural-voxel-isolated.json',dict(passed=True,occupied_voxels=int(voxel.sum()),voxel_matches_reference=True))
 print('PyCUDA voxelizer completed; normal interpreter exit follows.',flush=True)
elif sys.argv[1]=='scatter':
 import torch,torch_scatter,numpy as np
 x=torch.tensor([1.,2.,3.,4.],device='cuda');idx=torch.tensor([0,1,0,1],device='cuda');actual=torch_scatter.scatter_add(x,idx);np.testing.assert_array_equal(actual.cpu().numpy(),[4,6]);torch.cuda.synchronize()
 save('checks/V30-clean-neural-scatter-isolated.json',dict(passed=True,scatter_result=actual.cpu().numpy().tolist()))
 print('torch-scatter completed; normal interpreter exit follows.',flush=True)
else:raise ValueError(sys.argv)
