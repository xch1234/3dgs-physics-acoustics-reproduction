"""Read-only before/after byte audit of existing projects, source and delivery files."""
import sys,json
from common import ROOT,AUDIT,save,digest
def paths():
    files=set(p for p in ROOT.iterdir() if p.is_file())
    for name in ('01_PhysGaussian','02_PAT','03_NeuralSound','reproduction'):
        for p in (ROOT/name).rglob('*'):
            if p.is_file() and not p.is_symlink() and '.git' not in p.parts and '__pycache__' not in p.parts and 'cache' not in p.parts:
                files.add(p)
    return sorted(files)
def main():
    phase=sys.argv[1];before=AUDIT/'original-files-before.json'
    if phase=='before':
        assert not before.exists();records={}
        for i,p in enumerate(paths()):
            records[p.relative_to(ROOT).as_posix()]=dict(bytes=p.stat().st_size,sha256=digest(p))
            if i%1000==0:print('HASHED',i,flush=True)
        save('original-files-before.json',records);print('SNAPSHOT',len(records),flush=True)
    else:
        records=json.loads(before.read_text(encoding='utf-8'));changed=[];missing=[]
        for i,(name,old) in enumerate(records.items()):
            p=ROOT/name
            if not p.exists():missing.append(name)
            elif p.stat().st_size!=old['bytes'] or digest(p)!=old['sha256']:changed.append(name)
            if i%1000==0:print('RECHECKED',i,flush=True)
        added=sorted(set(p.relative_to(ROOT).as_posix() for p in paths())-set(records))
        result=dict(passed=not(changed or missing or added),files=len(records),changed=changed,missing=missing,added=added,excluded=['Conda installations','.git internals','__pycache__','runtime cache directories','new verification_20261101 directory'])
        save('original-files-after.json',result);print(json.dumps(result),flush=True)
        if not result['passed']:raise SystemExit(1)
if __name__=='__main__':main()
