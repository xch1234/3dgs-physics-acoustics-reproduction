import json,sys
import numpy as np
from PIL import Image
from common import AUDIT,save
folder=AUDIT/'physics/outputs/vasedeck_corrected_rerun'
m=json.loads((folder/'metrics.json').read_text())
rows=[]
for p in sorted((folder/'same_state_comparison').glob('*_raw.npz')):
 data=dict(np.load(p));a=data['original'];b=data['corrected'];frame=int(data['frame'])
 row=dict(frame=frame,shape=list(a.shape),expected=m['sh_same_state_comparison'][frame-1]['relative_image_L2'],numpy_float32=float(np.linalg.norm(b-a)/np.linalg.norm(a)),numpy_float64=float(np.linalg.norm(b.astype(float)-a)/np.linalg.norm(a.astype(float))),pixels={})
 for name,v in [('original',a),('corrected',b)]:
  pred=np.clip(np.moveaxis(v,0,-1)*255+.5,0,255).astype(np.uint8)
  with Image.open(folder/'same_state_comparison'/f'frame_{frame:04d}_{name}.png') as im:actual=np.array(im.convert('RGB'))
  delta=np.abs(actual.astype(int)-pred.astype(int))
  row['pixels'][name]=dict(max_difference=int(delta.max()),pixels_above_one=int((delta>1).sum()),range=[float(v.min()),float(v.max())])
 rows.append(row);print(row,flush=True)
save('checks/SH-artifact-diagnostic-'+('windows' if sys.platform=='win32' else 'linux')+'.json',rows)
