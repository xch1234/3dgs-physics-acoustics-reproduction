"""Restore released binary artifacts without touching existing mismatching files."""
from pathlib import Path
import argparse,hashlib,json,shutil,urllib.request,zipfile
ROOT=Path(__file__).resolve().parents[1]
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prefix',default='');ap.add_argument('--all',action='store_true');ap.add_argument('--list',action='store_true');ap.add_argument('--cache',type=Path,default=ROOT/'.artifact-cache');ap.add_argument('--destination',type=Path,default=ROOT);ap.add_argument('--manifest',type=Path,default=ROOT/'sharing/artifacts.json',help='Use sharing/remediation-artifacts.json for the November 2 supplement.');a=ap.parse_args()
 m=json.loads(a.manifest.read_text(encoding='utf8'));files=[x for x in m['files'] if x['path'].startswith(a.prefix)]
 if not files:raise SystemExit('No matching paths')
 if a.list:
  for f in files:print(f"{f['size']:>12}  {f['path']}")
  return
 if not a.all and not a.prefix:raise SystemExit('Choose --prefix PATH or --all; use --list first.')
 target=a.destination.resolve();target.mkdir(parents=True,exist_ok=True);a.cache.mkdir(parents=True,exist_ok=True)
 pending=[]
 for f in files:
  p=(target/f['path']).resolve()
  if not p.is_relative_to(target):raise ValueError('Unsafe manifest path')
  if p.exists():
   if digest(p)!=f['sha256']:raise RuntimeError(f'Refusing to overwrite differing file: {p}')
  else:pending.append(f)
 needed={m['chunks'][c]['asset'] for f in pending for c in f['chunks']};meta={x['name']:x for x in m['assets']}
 print(f'{len(pending)} files; {len(needed)} archives; {sum(meta[n]["size"] for n in needed)/2**30:.2f} GiB downloads before cache')
 for name in sorted(needed):
  p=a.cache/name;spec=meta[name]
  if p.exists() and digest(p)==spec['sha256']:continue
  url=f"https://github.com/{m['repo']}/releases/download/{m['tag']}/{name}";tmp=p.with_suffix('.part');print('Downloading',name,flush=True)
  req=urllib.request.Request(url,headers={'User-Agent':'reproduction-artifact-downloader'})
  with urllib.request.urlopen(req,timeout=180) as r,tmp.open('wb') as out:shutil.copyfileobj(r,out)
  if tmp.stat().st_size!=spec['size'] or digest(tmp)!=spec['sha256']:raise RuntimeError(f'Archive checksum mismatch: {name}')
  tmp.replace(p)
 handles={}
 try:
  for f in pending:
   p=target/f['path'];p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.restore-part');h=hashlib.sha256()
   with tmp.open('wb') as out:
    for c in f['chunks']:
     name=m['chunks'][c]['asset']
     if name not in handles:handles[name]=zipfile.ZipFile(a.cache/name)
     part=hashlib.sha256();size=0
     with handles[name].open(c) as src:
      while b:=src.read(4*2**20):out.write(b);h.update(b);part.update(b);size+=len(b)
     if part.hexdigest()!=c or size!=m['chunks'][c]['size']:raise RuntimeError('Chunk mismatch')
   if h.hexdigest()!=f['sha256'] or tmp.stat().st_size!=f['size']:raise RuntimeError(f'File mismatch: {p}')
   tmp.replace(p);print('Restored',f['path'],flush=True)
 finally:
  for z in handles.values():z.close()
if __name__=='__main__':main()
