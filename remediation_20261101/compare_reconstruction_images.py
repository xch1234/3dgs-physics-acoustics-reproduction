"""Fixed-view visual comparison; compare identical reference image bytes."""
from common import ROOT,AUDIT,save,digest
from PIL import Image,ImageOps,ImageDraw
import numpy as np
old=ROOT/'verification_20261101/outputs/ficus_fresh_30000/test/ours_30000'
new=AUDIT/'physics/outputs/ficus_anisotropy/test/ours_30000'
names=sorted(p.name for p in (old/'gt').glob('*.png'))
assert len(names)==200 and names==sorted(p.name for p in (new/'gt').glob('*.png'))
assert all(digest(old/'gt'/name)==digest(new/'gt'/name) for name in names)
canvas=Image.new('RGB',(1200,1690),'white');draw=ImageDraw.Draw(canvas)
for j,text in enumerate(['Reference / identical 200-view data','Independent baseline 30000','Fresh anisotropy 30000']):draw.text((j*400+8,8),text,fill='black')
rows=[]
for row,i in enumerate([0,50,100,150]):
 name=names[i];ref=np.asarray(Image.open(old/'gt'/name).convert('RGB')).astype(float)/255
 for col,path in enumerate([old/'gt'/name,old/'renders'/name,new/'renders'/name]):
  with Image.open(path) as im:
   arr=np.asarray(im.convert('RGB')).astype(float)/255
   assert arr.shape==ref.shape
   mae=float(np.abs(arr-ref).mean())
   canvas.paste(ImageOps.contain(im.convert('RGB'),(400,400)),(col*400,35+row*410))
   draw.text((col*400+8,20+row*410),name+f' / RGB MAE={mae:.6f}',fill='black')
   rows.append(dict(view=name,column=col,path=str(path),mean_absolute_RGB_error=mae))
canvas.save(AUDIT/'figures/ficus_reconstruction_comparison.png')
save('checks/V28-image-comparison.json',dict(passed=True,all_200_reference_images_byte_identical=True,views_selected_in_advance=[0,50,100,150],records=rows,scope='Visual comparison of fixed held-out views, not deformation truth. Aggregate metrics remain in separate evaluator outputs.'))
print('All 200 reference images identical; saved fixed-view comparison.')
