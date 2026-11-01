"""Isolated reruns of existing GPU experiments; no existing outputs overwritten."""
import os,sys,json,importlib,shutil
from pathlib import Path
from common import ROOT,AUDIT,save
os.environ['PHYSGAUSSIAN_SOURCE']='/opt/3dgs-runtime/PhysGaussian-source'
task=sys.argv[1]
if task=='vibration':
 sys.path.insert(0,str(ROOT/'03_NeuralSound/code'));import train_vibration as m
 isolated=AUDIT/'neural';(isolated/'outputs').mkdir(parents=True,exist_ok=True);(isolated/'docs').mkdir(exist_ok=True)
 if not (isolated/'inputs').exists():(isolated/'inputs').symlink_to(ROOT/'03_NeuralSound/inputs',target_is_directory=True)
 m.ROOT=isolated;sys.argv=[str(m.__file__),*sys.argv[2:]];m.main()
elif task=='scene':
 sys.path.insert(0,str(ROOT/'01_PhysGaussian/code'));import run_official_linux as m
 import warp as wp
 wp.config.kernel_cache_dir='/opt/3dgs-runtime/remediation-warp-cache'
 isolated=AUDIT/'physics';(isolated/'outputs').mkdir(parents=True,exist_ok=True);(isolated/'docs').mkdir(exist_ok=True)
 m.ROOT=isolated;sys.argv=[str(m.__file__),*sys.argv[2:]]
 if '--correct-sh-frame' not in sys.argv:sys.argv.append('--legacy-sh-frame')
 m.main()
elif task=='sh':
 sys.path.insert(0,str(ROOT/'01_PhysGaussian/code'));import validate_sh_frame as m
 isolated=AUDIT/'physics';(isolated/'outputs').mkdir(parents=True,exist_ok=True);(isolated/'docs').mkdir(exist_ok=True);m.ROOT=isolated;m.main()
else:raise ValueError(task)
