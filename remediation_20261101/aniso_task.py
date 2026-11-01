"""Redirect only local adapter I/O, keeping original trainer code and data."""
import sys
from common import ROOT,AUDIT
sys.path.insert(0,str(ROOT/'01_PhysGaussian/code'))
import train_with_anisotropy as train
train.ROOT=AUDIT/'physics';(train.ROOT/'docs').mkdir(parents=True,exist_ok=True)
train.main()
