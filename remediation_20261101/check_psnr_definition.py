"""Explain an observed PSNR discrepancy using two formulas on identical PNGs."""
import re,json
import numpy as np
from PIL import Image
from common import ROOT,AUDIT,save,digest
p=AUDIT/'physics/outputs/ficus_anisotropy/test/ours_30000'
rows=[]
for file in sorted((p/'renders').glob('*.png')):
 with Image.open(file) as im:a=np.asarray(im.convert('RGB')).astype(np.float64)/255
 with Image.open(p/'gt'/file.name) as im:b=np.asarray(im.convert('RGB')).astype(np.float64)/255
 mse=np.mean((a-b)**2,axis=(0,1));combined=float(-10*np.log10(mse.mean()));channelwise=float(np.mean(-10*np.log10(mse)))
 assert channelwise+1e-10>=combined
 rows.append(dict(view=file.name,global_RGB_PSNR=combined,mean_channel_PSNR=channelwise))
assert len(rows)==200
combined=float(np.mean([r['global_RGB_PSNR'] for r in rows]));channelwise=float(np.mean([r['mean_channel_PSNR'] for r in rows]))
reference=json.loads((AUDIT/'evaluations/anisotropy_30000/metrics.json').read_text())['mean']['PSNR'];assert abs(combined-reference)<1e-8
log=(AUDIT/'logs/V28-aniso-train.log').read_text(encoding='utf8');matches=re.findall(r'\[ITER 30000\] Evaluating test: L1 [\d.e+-]+ PSNR ([\d.e+-]+)',log);assert len(matches)==1
native=float(matches[0]);sources=['train.py','metrics.py','utils/image_utils.py'];repo=ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting'
result=dict(passed=True,images=200,PNG_global_RGB_PSNR=combined,PNG_mean_channel_PSNR=channelwise,training_float_tensor_channel_PSNR=native,channel_aggregation_difference_dB=channelwise-combined,training_minus_PNG_channelwise_dB=native-channelwise,source_hashes={s:digest(repo/s) for s in sources},records=rows,
 scope='Original train.py passes CHW to psnr(), which flattens dimension 0 as independent channels and then averages dB. metrics.py adds a batch axis and computes all-RGB MSE before log. Independent calculations on the SAME PNGs isolate that aggregation difference. The remaining small float-training vs PNG difference is reported, not asserted zero.')
save('checks/V28-psnr-definition.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ['records','source_hashes']},indent=2))
