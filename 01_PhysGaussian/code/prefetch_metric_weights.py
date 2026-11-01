"""Cache the public metric network weights without occupying GPU memory."""
import os,sys,json,hashlib
from pathlib import Path
os.environ['TORCH_HOME']='/opt/3dgs-runtime/torch-cache'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code/PhysGaussian/gaussian-splatting'))
from lpipsPyTorch import LPIPS
model=LPIPS(net_type='vgg',version='0.1').eval()
records=[]
for path in sorted(Path(os.environ['TORCH_HOME']).rglob('*')):
    if path.is_file():records.append(dict(file=str(path),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(ROOT/'docs/metric-weights.json').write_text(json.dumps(dict(scope='public VGG16 ImageNet and LPIPS 0.1 weights used only for reconstruction evaluation',files=records),indent=2))
print('Cached LPIPS VGG model on CPU',flush=True)
