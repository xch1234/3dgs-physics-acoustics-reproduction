import sys
from common import ROOT,AUDIT
sys.path.insert(0,str(ROOT/'01_PhysGaussian/code'))
import validate_sh_frame as m
m.ROOT=AUDIT/'windows_phys';(m.ROOT/'outputs').mkdir(parents=True,exist_ok=True);(m.ROOT/'docs').mkdir(exist_ok=True)
m.main()
