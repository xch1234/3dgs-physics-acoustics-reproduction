"""Read-only compact progress; never launches or interrupts jobs."""
import json
from pathlib import Path
A=Path(__file__).resolve().parent
for name in ['gpu-queue','gpu-followup','gpu-final','post-gpu','unified-neural','clean-pat']:
 p=A/(name+'-complete.json')
 if p.exists():
  d=json.loads(p.read_text());print(name+' COMPLETE '+str({k:v for k,v in d.items() if k!='jobs' or isinstance(v,int)}))
for stem in ['V28-radiation-paper_schedule','V26-radiation-longer','V28-aniso-train','V28-aniso-render']:
 p=A/'logs'/(stem+'.log')
 if p.exists() and not (A/'commands'/(stem+'.json')).exists():
  with p.open('rb') as f:
   f.seek(max(0,p.stat().st_size-3000));text=f.read().decode('utf8','replace')
  lines=[s for s in text.replace('\r','\n').splitlines() if s.strip()]
  print(stem+': '+(lines[-1][-350:] if lines else '(initializing)'))
for name in ['gpu-queue-state','gpu-followup-state','gpu-final-state']:
 p=A/(name+'.json')
 if p.exists():
  d=json.loads(p.read_text());print(name+': finished '+str(len(d))+', last '+str(d[-1]['name'])+', failures '+str([r['name'] for r in d if r.get('exit_code')!=0]))
for folder in (A/'physics/outputs').glob('*'):
 p=folder/'frame-audit.json'
 if p.exists() and not (folder/'metrics.json').exists():
  try:
   d=json.loads(p.read_text());print('Active scene '+folder.name+': audited frames '+str(len(d)))
  except json.JSONDecodeError:pass
for p in sorted((A/'logs').glob('V28-neural-*.log')):
 if not (A/'commands'/(p.stem+'.json')).exists():
  with p.open('rb') as f:
   f.seek(max(0,p.stat().st_size-1500));lines=f.read().decode('utf8','replace').replace('\r','\n').splitlines()
  print('Active '+p.stem+': '+(' '.join(lines[-2:])[-300:]))
