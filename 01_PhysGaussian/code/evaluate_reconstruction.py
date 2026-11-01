"""Memory-bounded evaluation using the exact public metric implementations."""
import argparse,json,sys,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps,ImageDraw
import torch
import torchvision.transforms.functional as tf
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'code/PhysGaussian/gaussian-splatting'))
from utils.loss_utils import ssim
from utils.image_utils import psnr
from lpipsPyTorch import LPIPS


def main():
    p=argparse.ArgumentParser();p.add_argument('--iteration',type=int,default=30000)
    p.add_argument('--output-dir',type=Path);args=p.parse_args()
    torch.set_grad_enabled(False);torch.set_num_threads(2)
    out=args.output_dir.resolve() if args.output_dir else ROOT/'outputs/ficus_reconstruction'
    out.relative_to((ROOT/'outputs').resolve())
    folder=out/f'test/ours_{args.iteration}'
    names=sorted((folder/'renders').glob('*.png'));assert len(names)==200,len(names)
    criterion=LPIPS(net_type='vgg',version='0.1').cuda().eval()
    rows=[];start=time.perf_counter();torch.cuda.reset_peak_memory_stats()
    for i,path in enumerate(names):
        with Image.open(path) as im:render=tf.to_tensor(im).unsqueeze(0)[:,:3].cuda()
        with Image.open(folder/'gt'/path.name) as im:gt=tf.to_tensor(im).unsqueeze(0)[:,:3].cuda()
        row=dict(image=path.name,SSIM=float(ssim(render,gt)),PSNR=float(psnr(render,gt).mean()),LPIPS=float(criterion(render,gt).mean()))
        assert all(np.isfinite(row[k]) for k in ('SSIM','PSNR','LPIPS')),row
        rows.append(row)
        if (i+1)%20==0:print('EVALUATED',i+1,row,flush=True)
    result=dict(test_images=len(rows),mean={k:float(np.mean([r[k] for r in rows])) for k in ('SSIM','PSNR','LPIPS')},
        per_image=rows,elapsed_s=time.perf_counter()-start,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
        protocol='original public metric functions on original render.py PNGs, LPIPS VGG 0.1; images streamed instead of retained together on GPU')
    (out/'evaluation.json').write_text(json.dumps(result,indent=2))
    canvas=Image.new('RGB',(1280,660),'white');draw=ImageDraw.Draw(canvas)
    for j,index in enumerate((0,50,100,150)):
        for row,part in enumerate(('gt','renders')):
            with Image.open(folder/part/names[index].name) as im:
                canvas.paste(ImageOps.contain(im.convert('RGB'),(320,320)),(320*j,330*row+20))
            draw.text((320*j+5,330*row+3),f'{part} / view {index}',fill='black')
    canvas.save(out/'heldout_comparison.jpg',quality=94)
    print(json.dumps(result['mean']),flush=True)


if __name__=='__main__':main()
