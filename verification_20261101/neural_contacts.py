import os
from common import AUDIT
os.environ['MPLCONFIGDIR']=str(AUDIT/'cache/matplotlib')
import numpy as np
from PIL import Image,ImageDraw
from matplotlib import colormaps
for tag in ('radiation_training','radiation_paper_schedule'):
    folder=AUDIT/'neural'/tag;a=np.load(folder/'predictions.npz')
    sheet=Image.new('RGB',(1120,672),'white');draw=ImageDraw.Draw(sheet)
    for i,(truth,pred,name,error) in enumerate(zip(a['reference'],a['predicted'],a['sample_names'],a['relative_L2'])):
        x=(i%4)*280;y=(i//4)*112
        draw.text((x+4,y+2),str(name)+' L2='+format(float(error),'.2f'),fill='black')
        draw.text((x+4,y+17),'BEM                    Prediction',fill='black')
        lo=min(0,float(pred.min()));hi=max(float(truth.max()),float(pred.max()))
        for j,m in enumerate((truth,pred)):
            rgb=(colormaps['viridis']((m.T-lo)/(hi-lo))[...,:3]*255).astype('uint8')
            im=Image.fromarray(rgb).resize((128,64),resample=Image.Resampling.NEAREST)
            sheet.paste(im,(x+4+j*138,y+34))
    sheet.save(folder/'all_test_maps.png')
    print(tag,'24 shared-scale pairs')
