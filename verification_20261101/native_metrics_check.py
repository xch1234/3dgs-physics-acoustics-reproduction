"""Try the unmodified all-views metrics entry point; detect its swallowed errors."""
import sys,json
from common import ROOT,AUDIT,run,runtime_env,save
prefix='/opt/3dgs-runtime/envs/physgaussian'
repo=ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting'
model=AUDIT/'outputs/ficus_fresh_30000'
assert not (model/'results.json').exists()
row=run('3dgs-native-metrics',[prefix+'/bin/python','-u',str(repo/'metrics.py'),'-m',str(model)],cwd=repo,env=runtime_env(prefix),timeout=600,required=False)
reference=json.loads((AUDIT/'evaluations/fresh_30000/metrics.json').read_text())['mean']
result=dict(command=row,native_script_exit_is_not_sufficient=True)
if (model/'results.json').exists():
    raw=json.loads((model/'results.json').read_text());values=raw.get('ours_30000',{})
    result.update(values=values,passed=all(k in values and abs(values[k]-v)<1e-4 for k,v in reference.items()))
else:
    result.update(passed=False,reason='Unmodified metrics.py did not produce results.json; inspect log (upstream catches exceptions without nonzero exit).')
save('checks/native-metrics.json',result)
print(json.dumps(result,indent=2),flush=True)
if not result['passed']:raise SystemExit(1)
