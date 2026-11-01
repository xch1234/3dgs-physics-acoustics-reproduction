import sys
from common import ROOT,AUDIT
sys.path.insert(0,str(ROOT/'01_PhysGaussian/code'))
import evaluate_reconstruction as m
m.ROOT=AUDIT/'physics';m.main()
