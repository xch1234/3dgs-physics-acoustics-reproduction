import json
from PIL import Image,ImageOps,ImageDraw
from common import AUDIT
m=json.loads((AUDIT/'evaluations/fresh_30000/metrics.json').read_text())
rows=sorted(m['per_image'],key=lambda r:r['PSNR'])[:4]
sheet=Image.new('RGB',(1280,680),'white');draw=ImageDraw.Draw(sheet)
for j,r in enumerate(rows):
    for i,kind in enumerate(('gt','renders')):
        with Image.open(AUDIT/'outputs/ficus_fresh_30000/test/ours_30000'/kind/r['image']) as im:
            sheet.paste(ImageOps.contain(im.convert('RGB'),(320,320)),(320*j,340*i+20))
        draw.text((320*j+4,340*i+3),kind+' '+r['image']+' PSNR='+format(r['PSNR'],'.3f'),fill='black')
sheet.save(AUDIT/'evaluations/fresh_30000/worst_views.jpg',quality=95)
print([(r['image'],r['PSNR']) for r in rows])
