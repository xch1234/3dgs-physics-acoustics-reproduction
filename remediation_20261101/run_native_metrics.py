from common import ROOT,AUDIT,run,runtime_env,save
import os,json,shutil
prefix='/opt/3dgs-runtime/envs/physgaussian';repo=ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting'
source=ROOT/'verification_20261101/outputs/ficus_fresh_30000';model=AUDIT/'outputs/native_metrics'
for kind in ('gt','renders'):
 dest=model/'test/ours_30000'/kind;dest.mkdir(parents=True,exist_ok=True)
 for src in (source/'test/ours_30000'/kind).glob('*.png'):
  if not (dest/src.name).exists():os.link(src,dest/src.name)
env=runtime_env(prefix);env['TORCH_HOME']=str(ROOT/'verification_20261101/cache/torch')
row=run('V12-original-metrics-all200',[prefix+'/bin/python','-u',str(repo/'metrics.py'),'-m',str(model)],cwd=repo,env=env,timeout=14400,required=False)
result={'command':row,'passed':False}
if (model/'results.json').exists():
 values=json.loads((model/'results.json').read_text())['ours_30000'];ref=json.loads((ROOT/'verification_20261101/evaluations/fresh_30000/metrics.json').read_text())['mean']
 per=json.loads((model/'per_view.json').read_text())['ours_30000']
 result.update(values=values,reference=ref,per_view_counts={k:len(v) for k,v in per.items()},passed=row['exit_code']==0 and all(abs(values[k]-ref[k])<1e-4 for k in ref) and all(len(v)==200 for v in per.values()))
save('checks/V12.json',result);print(json.dumps(result,indent=2),flush=True)
