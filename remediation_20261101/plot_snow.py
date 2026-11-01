from common import ROOT,AUDIT,save
import numpy as np,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw
out=AUDIT/'figures';out.mkdir(exist_ok=True)
d=np.load(AUDIT/'snow/load_unload.npz');spatial=np.load(AUDIT/'snow/spatial_final.npz')
old=np.load(ROOT/'01_PhysGaussian/outputs/material_audit/snow.npz');assert np.max(np.abs(old['stress_Pa']))==0
fig,axes=plt.subplots(1,3,figsize=(14,4),layout='constrained')
axes[0].plot(d['gamma'][:101],d['stress'][:101,0,1],label='Local snow / load')
axes[0].plot(d['gamma'][100:],d['stress'][100:,0,1],'--',label='Local snow / unload')
axes[0].axhline(0,color='gray',label='Released missing branch')
axes[0].set(xlabel='Prescribed shear',ylabel='Kirchhoff shear stress (Pa)',title='Local constitutive extension');axes[0].legend(fontsize=8)
axes[1].plot(d['gamma'][:101],d['Jp'][:101],label='Load');axes[1].plot(d['gamma'][100:],d['Jp'][100:],'--',label='Unload');axes[1].set(xlabel='Prescribed shear',ylabel='Plastic volume ratio Jp',title='Plastic history');axes[1].legend()
axes[2].plot(spatial['time_s'],spatial['trajectory'][:,:,2].min(1),label='Lowest particle center');axes[2].axhline(.25,color='gray',ls=':',label='Grid collider plane');axes[2].set(xlabel='Time (s)',ylabel='Height',title='125-particle gravity/contact check');axes[2].legend(fontsize=8)
fig.savefig(out/'snow_validation.png',dpi=150);plt.close(fig)
source=AUDIT/'physics/outputs/snow_ficus_local';canvas=Image.new('RGB',(1152,420),'white');draw=ImageDraw.Draw(canvas)
draw.text((12,8),'Ficus GEOMETRY with LOCAL snow material / not calibrated plant or snow physics',fill='black')
for j,index in enumerate([0,12,24]):
 with Image.open(source/f'{index:04d}.png') as im:canvas.paste(im.convert('RGB').resize((384,384)),(384*j,32))
 draw.text((384*j+12,34),f't={(index+1)*.04:.2f} s',fill='black')
canvas.save(out/'snow_ficus_contact_sheet.png')
save('checks/snow-figures.json',dict(files=['figures/snow_validation.png','figures/snow_ficus_contact_sheet.png'],scope='Plots from new raw stress/particle arrays and actual full CUDA-rendered frames.'))
