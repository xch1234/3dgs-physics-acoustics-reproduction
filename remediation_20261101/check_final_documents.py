"""Check final local navigation and evidence gates without changing results."""
import json,re
from urllib.parse import unquote
from common import ROOT,AUDIT,save

state=json.loads((AUDIT/'最终验收状态.json').read_text(encoding='utf8'))
assert len(state['items'])==11
assert state['counts']=={s:sum(x['status']==s for x in state['items']) for s in ['通过','失败','未验证']}
assert state['paper_reproduction_success'] is False
assert state['artifact_audit_passed'] and state['source_audit_passed']
files=[AUDIT/p for p in ['补做验收报告.md','本轮结果查看指南.md','命令与输出索引.md','README.md','可视化人工核查.md']]+[ROOT/'本轮补做入口.md']
links=[];errors=[]
for file in files:
 text=file.read_text(encoding='utf8')
 for target in re.findall(r'\]\(([^)]+)\)',text):
  if target.startswith(('http:','https:','#')):continue
  path=file.parent/unquote(target.split('#')[0].strip('<>'))
  links.append(dict(document=str(file.relative_to(ROOT)),target=target,exists=path.exists()))
  if not path.exists():errors.append(links[-1])
for item in state['items']:
 for path in item['evidence']:
  if not (AUDIT/path).exists():errors.append(dict(item=item['id'],missing=path))
save('checks/final-documents.json',dict(passed=not errors,files=[str(p.relative_to(ROOT)) for p in files],local_links_checked=len(links),errors=errors,scope='Local navigation, item counts and prerequisite evidence gates; not a replacement for scientific or visual review.'))
print('Checked',len(links),'local links; errors:',errors,flush=True)
if errors:raise SystemExit(1)
