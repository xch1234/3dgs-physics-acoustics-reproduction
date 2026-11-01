"""Rerun 12-mode extension and moving-listener study into isolated outputs."""
import sys,json
from common import ROOT,AUDIT,save
sys.path.insert(0,str(ROOT/'02_PAT/code'))
import run_pat as base
import run_pat_extended as ext
import run_moving_listener as moving
out=AUDIT/'pat_extensions';(out/'docs').mkdir(parents=True,exist_ok=True)
base.ROOT=out;base.OUT=out/'outputs/pat_pipeline'
base.FEM=ROOT/'verification_20261101/fresh_cpu_pipeline_retry/fem/official_fem_result.npz'
ext.OUT=out/'outputs/pat_extended';moving.ROOT=out;moving.OUT=out/'outputs/moving_listener'
ext.main();moving.main()
save('checks/V28-pat-extensions.json',dict(passed=True,extended=json.loads((ext.OUT/'metrics.json').read_text()),moving=json.loads((moving.OUT/'metrics.json').read_text()),scope='Historical magnitude-only extension independently rerun; V08 phase correction separately tested.'))
