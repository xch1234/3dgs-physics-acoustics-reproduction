import sys,os,json,re,subprocess
from common import ROOT,AUDIT,save,stamp
query="$ErrorActionPreference='Stop'; $r=@(Get-CimInstance Win32_Process -Filter \"Name = 'python.exe'\" | Where-Object { $_.CommandLine -like '*verification_20261101*' } | Select-Object ProcessId,ParentProcessId,CommandLine); ConvertTo-Json -InputObject $r -Compress"
raw=subprocess.check_output(['powershell.exe','-NoProfile','-Command',query]).decode('utf-8',errors='replace')
processes=json.loads(raw or '[]');remaining=[]
for p in processes:
    if p['ProcessId'] in (os.getpid(),os.getppid()):continue
    match=re.search(r'verification_20261101[\\/]([a-zA-Z_]+\.py)',p.get('CommandLine') or '')
    remaining.append(dict(pid=p['ProcessId'],script=match.group(1) if match else 'unclassified audit Python process'))
proc=subprocess.run(['wsl.exe','-d','Ubuntu1','--','ps','-eo','pid,args'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
linux=[s for s in proc.stdout.decode('utf-8',errors='replace').splitlines() if 'verification_20261101' in s]
gpu=subprocess.run(['wsl.exe','-d','Ubuntu1','--','nvidia-smi','--query-gpu=memory.used,memory.total,utilization.gpu','--format=csv,noheader'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
result=dict(timestamp=stamp(),remaining_windows_audit_jobs=remaining,remaining_linux_audit_jobs=linux,own_jobs_finished=not(remaining or linux),GPU_query_exit=gpu.returncode,GPU_status=gpu.stdout.decode(errors='replace').strip(),note='The current inspection script and its direct capture parent are excluded; no user process is stopped.')
save('checks/runtime-final.json',result)
print(json.dumps(result,ensure_ascii=False,indent=2))
assert result['own_jobs_finished']
