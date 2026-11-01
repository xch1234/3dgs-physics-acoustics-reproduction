"""Run the unchanged Windows constitutive test with only output/cache redirection."""
import sys
from common import ROOT,AUDIT
sys.path.insert(0,str(ROOT/'01_PhysGaussian/code'))
import warp as wp
import validate_materials as m
m.ROOT=AUDIT/'materials'
(m.ROOT/'outputs').mkdir(parents=True,exist_ok=True)
(m.ROOT/'docs').mkdir(exist_ok=True)
wp.config.kernel_cache_dir=str(AUDIT/'cache/warp_windows')
m.main()
