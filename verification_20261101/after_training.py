"""Wait for this validation's fresh training, then run GPU checks sequentially."""
import time,json,sys
from common import ROOT,AUDIT,run,runtime_env,save
def main():
    state={'status':'waiting for current fresh 3DGS pipeline','stages':[]};save('followup-state.json',state)
    while True:
        path=AUDIT/'3dgs-state.json'
        if path.exists():
            upstream=json.loads(path.read_text())
            if upstream['status']=='completed':break
            if upstream['status']=='failed':state['status']='blocked by failed fresh training';save('followup-state.json',state);raise SystemExit(1)
        time.sleep(5)
    phys='/opt/3dgs-runtime/envs/physgaussian';neural='/opt/3dgs-runtime/envs/neuralsound'
    jobs=[('physics-sh',[phys+'/bin/python','-u',str(AUDIT/'physics_isolated.py'),'sh'],phys),
          ('physics-transport',[phys+'/bin/python','-u',str(AUDIT/'physics_isolated.py'),'transport'],phys),
          ('physics-fresh-full',[phys+'/bin/python','-u',str(AUDIT/'physics_isolated.py'),'simulation'],phys),
          ('neural-fresh-inference',[neural+'/bin/python','-u',str(AUDIT/'neural_inference.py')],neural),
          ('vibration-fresh-solves',[neural+'/bin/python','-u',str(AUDIT/'vibration_rerun.py')],neural),
          ('cuda-source-build',[phys+'/bin/python','-u',str(AUDIT/'build_cuda.py')],phys)]
    for name,cmd,prefix in jobs:
        state['status']=name;save('followup-state.json',state)
        result=run(name,cmd,env=runtime_env(prefix),required=False);state['stages'].append(result);save('followup-state.json',state)
    state['status']='completed';save('followup-state.json',state)
if __name__=='__main__':main()
