"""Observe swallowed exceptions from unchanged upstream metrics.py, if needed."""
import sys,runpy,json,os
from common import ROOT,AUDIT,save,runtime_env
os.environ.update(runtime_env('/opt/3dgs-runtime/envs/physgaussian'))
source=ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting/metrics.py'
events=[]
def trace(frame,event,arg):
    if frame.f_code.co_filename==str(source):
        if event=='exception':
            kind,value,tb=arg
            row=dict(type=kind.__name__,message=str(value),function=frame.f_code.co_name,line=frame.f_lineno)
            events.append(row);print('OBSERVED_UPSTREAM_EXCEPTION',row,flush=True)
        return trace
    return None
sys.path.insert(0,str(source.parent))
sys.argv=[str(source),'-m',str(AUDIT/'outputs/ficus_fresh_30000')]
sys.settrace(trace)
try:runpy.run_path(str(source),run_name='__main__')
finally:
    sys.settrace(None);save('checks/native-metrics-exceptions.json',events)
