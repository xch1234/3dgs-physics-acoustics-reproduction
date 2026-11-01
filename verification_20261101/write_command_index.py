"""Create a human-readable index of actual command records, including failures."""
import json,shlex
from common import AUDIT,save,stamp
rows=[]
for p in sorted((AUDIT/'commands').glob('*.json')):
    row=json.loads(p.read_text(encoding='utf-8'));row['record']=p.relative_to(AUDIT).as_posix();rows.append(row)
lines=['# 独立验证命令索引','',f'生成时间：{stamp()}。本文件仅整理本轮真实执行记录；非零退出和未启动成功的尝试均保留。','',
'命令以 argv 数组记录在每个 JSON 中，下方引号为便于阅读生成的 POSIX 表示；Windows 调用应以 JSON 参数数组为准。日志包含关键输出的完整上下文。','']
for r in rows:
    log=r['log'].replace('\\','/')
    lines.extend([f'## {r["name"]}', '',f'- 退出码：`{r.get("exit_code")}`；耗时：{r.get("elapsed_s",0):.3f} 秒。',f'- 开始：{r.get("started","未记录")}；结束：{r.get("finished","未记录")}。',f'- 工作目录：`{r["cwd"]}`。',f'- [原始记录]({r["record"]})；[日志]({log})。','', '```text',shlex.join(r['command']),'```',''])
    if r.get('error'):lines.extend(['启动/执行异常：`'+r['error']+'`',''])
lines.extend(['## 直接执行并保存日志的补充检查','',
'以下命令在工作目录 `F:/System/Desktop/3DGS/复现` 执行。退出状态来自本轮终端结果；这些直接调用未使用统一时间记录器，不补造起止时间。','',
'- `.conda/acoustics/python.exe verification_20261101/independent_cpu.py`：退出 0；[日志](independent-cpu.log)，[五组检查](checks/cpu-suite.json)。',
'- `.conda/acoustics/python.exe verification_20261101/audio_readback.py`：退出 0；[日志](audio-readback.log)，[PCM 检查](checks/audio-readback.json)。',
'- `.conda/acoustics/python.exe verification_20261101/check_git_lineendings.py`：退出 0；[日志](git-lineendings.log)，[逐文件与 HEAD 比较](checks/git-lineendings.json)。',
'- `.conda/acoustics/python.exe verification_20261101/compare_fem_modes.py`：退出 0 表示检查成功执行；它检测出的音频不变性为失败。见 [日志](fem-basis-audio.log)、[指标](checks/fem-basis-audio-invariance.json)。',
'- `C:/ProgramData/anaconda3/python.exe verification_20261101/read_papers.py`：退出 0；[提取日志](paper-extraction.log)，[PDF 哈希及页数](papers/sources.json)。另实际渲染并查看 NeuralSound 第 10 页。',
'- `.conda/acoustics/python.exe verification_20261101/snapshot_originals.py before`：退出 0；[日志](snapshot-before.log)，[9166 文件初始哈希](original-files-before.json)。',
'- `.conda/acoustics/python.exe verification_20261101/check_manifest_and_metadata.py`：退出 0 表示核查完成；Windows 环境导出路径编码检查检测到缺陷。见 [日志](manifest-and-metadata.log)、[路径记录](checks/environment-export-text.json)。',
'', '首次 WSL 进程启动错误和 PowerShell 对 WSL stderr 的包装错误详见 [补充环境检查说明](补充环境检查说明.md)。不要仅凭最外层 PowerShell 的状态，推断科学检查成功或失败；本索引保留子进程退出码与实际产物检查。',''])
(AUDIT/'命令与日志索引.md').write_text('\n'.join(lines),encoding='utf-8')
save('command-index.json',rows)
print('Indexed commands',len(rows))
