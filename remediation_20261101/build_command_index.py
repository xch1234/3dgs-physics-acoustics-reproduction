"""Generate a navigable execution record from actual command JSON and logs."""
import json,shlex,re
from common import AUDIT,save
rows=[]
for p in (AUDIT/'commands').glob('*.json'):
 d=json.loads(p.read_text(encoding='utf-8-sig'));d['record_file']=p.relative_to(AUDIT).as_posix()
 # Early launchers recorded argv/exit/seconds without wall-clock timestamps.
 # Normalize for display only; never fabricate missing execution metadata.
 if 'name' not in d:
  d['name']=p.stem;d['command']=d.get('argv',[]);d['exit_code']=d.get('exit')
  d['elapsed_s']=d.get('elapsed_seconds',d.get('seconds',0))
  d['cwd']='未单独记录；早期启动器继承父进程工作目录'
  stem={'V08':'V08-phase-audio','V30-create':'V30-conda-clean-create'}.get(p.stem,p.stem)
  if (AUDIT/'logs'/(stem+'.log')).exists():d['log']='logs/'+stem+'.log'
 rows.append(d)
rows.sort(key=lambda d:(d.get('started',''),d['name']))
lines=['# 本轮实际执行命令索引','',
 '由 `commands/*.json` 和实际日志生成。退出码 0 只证明该命令正常退出，不代表误差达标或论文完整复现。失败的下载、初次环境诊断和重试均保留；最终科学结论见补做验收报告。', '',
 '下列命令使用各自记录的工作目录。Linux 命令须在 Ubuntu1 的 WSL 内运行，Windows 命令使用 PowerShell。重建环境的命令要求新前缀；任务仍运行时不要重复执行队列。参数数组以每项原始 JSON 为准。','']
for d in rows:
 argv=d.get('command',[]);linux=bool(argv and str(argv[0]).startswith('/'))
 command=shlex.join(argv) if linux else '& '+' '.join("'"+str(v).replace("'","''")+"'" for v in argv)
 lines += ['## '+d['name'],'',f"- 开始：{d.get('started','未记录')}；结束：{d.get('finished','未记录')}；耗时：{d.get('elapsed_s',0):.2f} 秒。",f"- 退出码：`{d.get('exit_code')}`；工作目录：`{d.get('cwd')}`。",f"- [原始记录]({d['record_file']})；[完整日志]({d.get('log','')})。",'', '```'+('bash' if linux else 'powershell'),command,'```','']
 log=AUDIT/d.get('log','')
 if log.is_file():
  raw=log.read_text(encoding='utf8',errors='replace').replace('\r','\n')
  meaningful=[s for s in raw.splitlines() if s.strip()]
  # Only quote actual output, never generate a synthetic success message.
  excerpt=meaningful[-10:]
  excerpt=[s[:500]+(' … [本行节选，完整见日志]' if len(s)>500 else '') for s in excerpt]
  lines += ['日志末尾关键输出（有截断时以完整日志为准）：','','```text',*excerpt,'```','']
supplement=AUDIT/'checks/supplemental-evidence-index.json'
if supplement.exists():
 lines += ['## 早期准备脚本的记录限制','', '以下是已有产物对应的可复跑入口。首轮完整 shell 参数与起止时间未单独保存，不能将这里的复跑写法冒充当时的原始命令。新环境构建、训练、模拟和评估的实际命令仍以上述独立 JSON 为准。','']
 for d in json.loads(supplement.read_text(encoding='utf8')):
  lines += [f"- `{d['producer']}`：`python remediation_20261101/{d['producer']}`；[结果]({d['evidence']})"+(f"；[已有日志]({d['existing_log']})" if d['existing_log'] else '；首轮终端日志未单独保留。')]
 lines += ['','[补充证据索引与哈希](checks/supplemental-evidence-index.json)。']
(AUDIT/'命令与输出索引.md').write_text('\n'.join(lines),encoding='utf8')
save('checks/command-index.json',dict(record_count=len(rows),nonzero_or_missing_exit=[d['name'] for d in rows if d.get('exit_code')!=0],scope='Execution metadata including failed attempts; not scientific acceptance.'))
print('Indexed',len(rows),'commands')
