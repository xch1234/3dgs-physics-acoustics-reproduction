import json,re,ast
from common import AUDIT,save
import write_final_report,write_command_index
native=json.loads((AUDIT/'checks/native-metrics.json').read_text(encoding='utf-8'))
if (AUDIT/'checks/native-entry-stop.json').exists():
    stop=json.loads((AUDIT/'checks/native-entry-stop.json').read_text(encoding='utf-8'))
    native.update(assessment='未验证',reason=f'Original entry stopped after {stop["completed_views"]}/200 views due excessive measured duration; see stop record. Full independent streaming evaluation completed separately.',stop_record='checks/native-entry-stop.json')
    save('checks/native-metrics.json',native)
runtime=json.loads((AUDIT/'checks/runtime-final.json').read_text(encoding='utf-8'));assert runtime['own_jobs_finished']
write_command_index.main() if hasattr(write_command_index,'main') else None
write_final_report.main()
p=AUDIT/'独立验证报告.md'
with p.open('a',encoding='utf-8') as f:f.write('\n## 7. 结束状态\n\n最终进程核对确认无本次遗留的 Windows/Linux 实验 Python 进程。见 [结束状态](checks/runtime-final.json) 和 [检查命令](commands/windows-runtime_final.json)。原始评估入口按记录停止，其余已执行实验正常收尾；没有停止用户的进程。\n')
p=AUDIT/'命令与日志索引.md'
with p.open('a',encoding='utf-8') as f:
    f.write('\n## 可视化整理命令\n\n以下均由 Windows `.conda/acoustics/python.exe` 实际执行，退出 0：\n\n- `verification_20261101/worst_views.py`：生成 [最低 PSNR 四图对照](evaluations/fresh_30000/worst_views.jpg)。\n- `verification_20261101/neural_contacts.py`：生成两套各 24 对全体测试图 [发布训练 profile](neural/radiation_training/all_test_maps.png)、[paper-schedule 本地对照](neural/radiation_paper_schedule/all_test_maps.png)。\n\n图像实际查看的范围与观察记录见 [可视化核查记录](可视化核查记录.md)。原 200 图 metrics.py 入口的实际停止命令、已完成数量和理由见 [停止记录](checks/native-entry-stop.json)，最终状态为未验证。\n')
documents=['独立验证报告.md','命令与日志索引.md','可视化核查记录.md','验收标准.md','补充环境检查说明.md']
missing=[];links=0
for name in documents:
    text=(AUDIT/name).read_text(encoding='utf-8')
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
        if target.startswith(('http:','https:','#')):continue
        links+=1
        if not (AUDIT/target.split('#')[0]).exists():missing.append(dict(document=name,target=target))
items=json.loads((AUDIT/'逐项验收.json').read_text(encoding='utf-8'));assert len(items)==32 and len({i['id'] for i in items})==32
assert all(i['status'] in ('通过','失败','未验证') for i in items)
for p in AUDIT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'))
save('checks/document-links.json',dict(documents=documents,links_checked=links,missing=missing,items=len(items),passed=not missing))
assert not missing,missing
print('Document links checked',links,'items',len(items))
