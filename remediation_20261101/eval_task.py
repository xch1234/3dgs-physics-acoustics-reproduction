import sys
from common import ROOT,AUDIT
sys.path.insert(0,str(ROOT/'verification_20261101'))
import evaluate_3dgs as evaluation
evaluation.AUDIT=AUDIT
evaluation.main()
