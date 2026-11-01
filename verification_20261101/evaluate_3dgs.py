"""Fresh evaluation and original-RGBA ground-truth verification; writes only audit outputs."""
import sys,json,argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps,ImageDraw
from common import ROOT,AUDIT,save,digest
sys.path.insert(0,str(ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting'))
import torch
from utils.loss_utils import ssim
from lpipsPyTorch import LPIPS

def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--tag',required=True);args=p.parse_args()
    folder=Path(args.model)/'test/ours_30000';out=AUDIT/'evaluations'/args.tag;out.mkdir(parents=True,exist_ok=True)
    source=ROOT/'01_PhysGaussian/inputs/nerf_synthetic_ficus'
    transforms=json.loads((source/'transforms_test.json').read_text())['frames']
    images=sorted((folder/'renders').glob('*.png'));assert len(images)==len(transforms)==200
    torch.set_num_threads(2);torch.set_grad_enabled(False);criterion=LPIPS(net_type='vgg',version='0.1').cuda().eval()
    rows=[]
    for i,path in enumerate(images):
        with Image.open(path) as im:r=np.array(im.convert('RGB'));assert im.size==(800,800)
        with Image.open(folder/'gt'/path.name) as im:g=np.array(im.convert('RGB'))
        raw=source/(transforms[i]['file_path']+'.png')
        with Image.open(raw) as im:rgba=np.array(im.convert('RGBA'),dtype=float)/255
        composed=(rgba[:,:,:3]*rgba[:,:,3:]+(1-rgba[:,:,3:]))*255
        # Dataset reader truncates to uint8 before torchvision saves the ground truth.
        expected=composed.astype(np.uint8)
        gt_diff=int(np.max(np.abs(g.astype(int)-expected.astype(int))))
        assert gt_diff<=1,(path,gt_diff)
        mse=np.mean(((r.astype(float)-g.astype(float))/255)**2)
        rt=torch.from_numpy(r.copy()).permute(2,0,1).float().unsqueeze(0).cuda()/255
        gt=torch.from_numpy(g.copy()).permute(2,0,1).float().unsqueeze(0).cuda()/255
        row=dict(image=path.name,source_image=str(raw.relative_to(ROOT)),PSNR=float(-10*np.log10(mse)),SSIM=float(ssim(rt,gt)),LPIPS=float(criterion(rt,gt).mean()),ground_truth_max_byte_difference=gt_diff)
        assert all(np.isfinite(row[k]) for k in ('PSNR','SSIM','LPIPS'));rows.append(row)
        if (i+1)%20==0:print(i+1,row,flush=True)
    result=dict(images=len(rows),mean={k:float(np.mean([r[k] for r in rows])) for k in ('PSNR','SSIM','LPIPS')},per_image=rows,model_sha256=digest(Path(args.model)/'point_cloud/iteration_30000/point_cloud.ply'),method='Independent NumPy RGB PNG PSNR; original SSIM and LPIPS-VGG; raw RGBA camera-order GT checked')
    save('evaluations/'+args.tag+'/metrics.json',result)
    canvas=Image.new('RGB',(1280,680),'white');draw=ImageDraw.Draw(canvas)
    for j,i in enumerate((0,50,100,150)):
        for row,part in enumerate(('gt','renders')):
            with Image.open(folder/part/images[i].name) as im:canvas.paste(ImageOps.contain(im.convert('RGB'),(320,320)),(j*320,row*340+20))
            draw.text((j*320+5,row*340+3),f'{part}: test view {i}',fill='black')
    canvas.save(out/'comparison.jpg',quality=95)
    print(json.dumps(result['mean']),flush=True)
if __name__=='__main__':main()
