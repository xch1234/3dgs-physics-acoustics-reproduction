import time,json
from common import ROOT,AUDIT,run,runtime_env,save
while True:
    p=AUDIT/'late-checks-state.json'
    if p.exists() and json.loads(p.read_text())['status']=='completed':break
    time.sleep(5)
row=run('materials-fresh-windows',[str(ROOT/'.conda/physgaussian/python.exe'),'-u',str(AUDIT/'materials_isolated.py')],env=runtime_env(),required=False)
save('last-windows-state.json',dict(status='completed',stages=[row]))
