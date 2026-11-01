import os,json,subprocess,time,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
AUDIT=Path(__file__).resolve().parent
ROOT=AUDIT.parent
def stamp():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def save(name,data):
    p=AUDIT/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def runtime_env(prefix=None):
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PYTHONUTF8='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
    for key,part in [('MPLCONFIGDIR','matplotlib'),('TMPDIR','tmp'),('CUDA_CACHE_PATH','cuda'),('PYCUDA_CACHE_DIR','pycuda'),('TORCH_EXTENSIONS_DIR','torch_extensions'),('TORCH_HOME','torch'),('XDG_CACHE_HOME','xdg'),('TI_OFFLINE_CACHE_FILE_PATH','taichi')]:
        p=AUDIT/'cache'/part;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
    if prefix:
        env['CUDA_HOME']=prefix;env['PATH']=prefix+'/bin:'+env['PATH'];env['LD_LIBRARY_PATH']='/usr/lib/wsl/lib:'+prefix+'/lib'
    return env
def run(name,argv,cwd=None,env=None,timeout=None,required=True):
    log=AUDIT/'logs'/f'{name}.log';log.parent.mkdir(exist_ok=True)
    row=dict(name=name,command=list(map(str,argv)),cwd=str(cwd or AUDIT),started=stamp(),log=str(log.relative_to(AUDIT)))
    print('START',name,flush=True);start=time.monotonic()
    try:
        with log.open('wb') as f:
            p=subprocess.run(row['command'],cwd=cwd or AUDIT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
        row['exit_code']=p.returncode
    except Exception as exc:row.update(exit_code=None,error=repr(exc))
    row.update(finished=stamp(),elapsed_s=time.monotonic()-start)
    save('commands/'+name+'.json',row)
    print('END',name,row.get('exit_code'),flush=True)
    if required and row.get('exit_code')!=0:raise RuntimeError(row)
    return row
