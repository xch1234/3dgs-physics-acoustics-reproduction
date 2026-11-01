from pathlib import Path
import json,shutil,re,hashlib
R=Path(__file__).resolve().parents[1];A=R/'remediation_20261101';records=[]
for name,env in [('01_PhysGaussian','physgaussian'),('02_PAT','acoustics'),('03_NeuralSound','acoustics')]:
 p=R/name/'docs/environment.yml';backup=A/'backups'/name/'environment.yml';backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,backup)
 s=p.read_text(encoding='utf-8-sig');before=s.count('\ufffd');s=re.sub(r'^name:.*$',f'name: reproduction-{env}',s,flags=re.M);s=re.sub(r'^prefix:.*\n?', '',s,flags=re.M)
 assert '\ufffd' not in s
 p.write_text(s,encoding='utf8');records.append({'path':str(p.relative_to(R)),'original_replacement_characters':before,'name':f'reproduction-{env}','prefix_removed':True,'backup':str(backup.relative_to(A))})
(A/'checks/V03-export-repair.json').write_text(json.dumps({'passed':True,'changes':records,'clean_environment_creation':'pending'},ensure_ascii=False,indent=2),encoding='utf8')
# Establish explicit scopes before further experiments.
items=json.loads((R/'verification_20261101/逐项验收.json').read_text(encoding='utf8'));items=[{'id':x['id'],'previous_status':x['status'],'title':x['title'],'new_status':'进行中'} for x in items if x['status']!='通过']
(A/'scope.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf8')
print('Repaired three exports; preserved original bytes in backups.')
