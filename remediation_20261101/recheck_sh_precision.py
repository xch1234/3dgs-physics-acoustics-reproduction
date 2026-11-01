"""Repeat all SH array/image checks in float64; preserve the failed full audit."""
import json
import numpy as np
from PIL import Image,ImageDraw,ImageOps
from common import AUDIT,ROOT,save,digest
initial=AUDIT/'checks/final-artifacts-first-attempt.json'
first=json.loads(initial.read_text(encoding='utf8'))
assert len(first['errors'])==1 and first['errors'][0]['item']=='vasedeck_corrected_rerun',first['errors']
assert len(first['video_and_scene_checks'])==19 and len(first['wav_checks'])==24
# Media/scene decoding and finite-state checks already ran in full. No producers
# are rerun here. Rehash saved media/models before reusing those completed checks.
for row in first['video_and_scene_checks']+first['wav_checks']:
 assert digest(AUDIT/row['path'])==row['sha256'],row['path']
models=[AUDIT/'physics/outputs/ficus_anisotropy/point_cloud/iteration_30000/point_cloud.ply',ROOT/'verification_20261101/outputs/ficus_fresh_30000/point_cloud/iteration_30000/point_cloud.ply']
for row,path in zip(first['models'],models):assert digest(path)==row['sha256']
rows=[]
for tag in ['bread','plane','vasedeck']:
 folder=AUDIT/'physics/outputs'/(tag+'_corrected_rerun')
 m=json.loads((folder/'metrics.json').read_text());files=sorted((folder/'same_state_comparison').glob('*_raw.npz'))
 assert m['sh_frame_correction'] and len(m['sh_same_state_comparison'])==m['rendered_frames'] and len(files)==4
 for path in files:
  raw=dict(np.load(path));a=raw['original'];b=raw['corrected'];frame=int(raw['frame'])
  assert np.isfinite(a).all() and np.isfinite(b).all()
  measured=float(np.linalg.norm(b.astype(np.float64)-a)/np.linalg.norm(a.astype(np.float64)))
  expected=m['sh_same_state_comparison'][frame-1]['relative_image_L2']
  assert abs(measured-expected)<1e-6,(tag,frame,measured,expected)
  pixels=[]
  for name,values in [('original',a),('corrected',b)]:
   p=folder/'same_state_comparison'/f'frame_{frame:04d}_{name}.png'
   with Image.open(p) as im:actual=np.array(im.convert('RGB'))
   expected_pixels=np.clip(np.moveaxis(values,0,-1)*255+.5,0,255).astype(np.uint8)
   delta=int(np.max(np.abs(actual.astype(int)-expected_pixels.astype(int))))
   assert delta<=1,(tag,frame,name,delta)
   pixels.append(dict(path=str(p.relative_to(AUDIT)),max_byte_difference=delta,sha256=digest(p)))
  rows.append(dict(scene=tag,frame=frame,shape=list(a.shape),float64_relative_L2=measured,recorded_relative_L2=expected,absolute_statistic_difference=abs(measured-expected),raw_sha256=digest(path),pixels=pixels))
  print(tag,frame,measured,expected,flush=True)
 canvas=Image.new('RGB',(960,345),'white');draw=ImageDraw.Draw(canvas)
 for j,(label,values) in enumerate(zip(['Original SH','Corrected SH','Absolute difference x20'],[a,b,np.clip(np.abs(b-a)*20,0,1)])):
  draw.text((j*320+8,7),tag+'_corrected_rerun / '+label,fill='black')
  im=Image.fromarray((np.moveaxis(values,0,-1).clip(0,1)*255).round().astype(np.uint8))
  canvas.paste(ImageOps.contain(im,(320,320)),(j*320,25))
 canvas.save(AUDIT/'figures'/(tag+'_corrected_rerun_same_state.jpg'),quality=95)
result=dict(passed=True,rows=rows,maximum_absolute_statistic_difference=max(r['absolute_statistic_difference'] for r in rows),unchanged_tolerance=1e-6,pixel_tolerance=1,scope='All 12 saved raw pairs and 24 PNGs rechecked with float64 norm accumulation. Original float32 CPU reduction audit retained; tolerances and simulation/rendered results unchanged. All 19 videos, 24 WAV and 2 PLY hashes reconfirmed before reusing completed decode/finite-state checks.')
save('checks/SH-artifact-precision-recheck.json',result)
final=dict(first);final.update(passed=True,errors=[],initial_audit='checks/final-artifacts-first-attempt.json',initial_audit_sha256=digest(initial),recovery='checks/SH-artifact-precision-recheck.json')
save('checks/final-artifacts.json',final)
print('All affected SH checks passed; full media results retained with recovery provenance.',flush=True)
