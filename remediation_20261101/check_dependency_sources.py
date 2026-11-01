"""Re-fetch fixed build dependencies and compare tracked source bytes."""
import io,json,tarfile,zipfile,requests
from common import ROOT,AUDIT,save,digest
base='01_PhysGaussian/code/PhysGaussian/gaussian-splatting'
items=[
 ('gaussian-splatting',base,'graphdeco-inria/gaussian-splatting','d9fad7b3450bf4bd29316315032d57157e23a515'),
 ('diff-gaussian-rasterization',base+'/submodules/diff-gaussian-rasterization','graphdeco-inria/diff-gaussian-rasterization','59f5f77e3ddbac3ed9db93ec2cfe99ed6c5d121d'),
 ('glm',base+'/submodules/diff-gaussian-rasterization/third_party/glm','g-truc/glm','5c46b9c07008ae65cb81ab79cd677ecc1934b903'),
 ('MinkowskiEngine','03_NeuralSound/code/MinkowskiEngine','NVIDIA/MinkowskiEngine','02fc608bea4c0549b0a7b00ca1bf15dee4a0b228'),
 ('simple-knn',base+'/submodules/simple-knn',None,'44f764299fa305faf6ec5ebd99939e0508331503'),
]
rows=[]
for name,local,repo,commit in items:
 url=(f'https://codeload.github.com/{repo}/tar.gz/{commit}' if repo else f'https://gitlab.inria.fr/bkerbl/simple-knn/-/archive/{commit}/simple-knn-{commit}.tar.gz')
 row=dict(name=name,commit=commit,url=url,local=local)
 try:
  r=requests.get(url,timeout=120);r.raise_for_status();p=AUDIT/'remote'/f'dependency-{name}.tar.gz';p.write_bytes(r.content)
  differences=[];count=0;newlines=0
  with tarfile.open(fileobj=io.BytesIO(r.content)) as t:
   for m in t:
    if not m.isfile():continue
    rel='/'.join(m.name.split('/')[1:]);f=ROOT/local/rel;b=t.extractfile(m).read();count+=1
    if not f.exists():differences.append(dict(file=rel,reason='missing'));continue
    a=f.read_bytes()
    if a!=b:
     if a.replace(b'\r\n',b'\n')==b.replace(b'\r\n',b'\n'):newlines+=1
     else:differences.append(dict(file=rel,reason='different bytes beyond CRLF'))
  row.update(passed=not differences,archive_sha256=digest(p),files=count,newline_only_differences=newlines,differences=differences)
 except Exception as e:row.update(passed=False,error=repr(e))
 rows.append(row);save('checks/V30-dependency-sources.json',dict(passed=all(x['passed'] for x in rows),records=rows,scope='Fixed remote dependency archives versus local files, allowing CRLF only; excludes unused SIBR viewer and binary wheels.'))
 print(name,row.get('files'),row['passed'],row.get('error',row.get('differences')),flush=True)
prov=json.loads((ROOT/'02_PAT/code/dependencies/eigen-provenance.json').read_text())
r=requests.get(prov['url'],timeout=120);r.raise_for_status();p=AUDIT/'remote/dependency-eigen-3.3.7.zip';p.write_bytes(r.content)
different=[];count=0
with zipfile.ZipFile(p) as z:
 for name in z.namelist():
  if name.endswith('/'):continue
  rel='/'.join(name.split('/')[1:]);f=ROOT/'02_PAT/code/dependencies/eigen-git-mirror-3.3.7'/rel;count+=1
  if not f.exists() or f.read_bytes().replace(b'\r\n',b'\n')!=z.read(name).replace(b'\r\n',b'\n'):different.append(rel)
rows.append(dict(name='Eigen',url=prov['url'],archive_sha256=digest(p),expected_sha256=prov['sha256'],files=count,differences=different,passed=not different and digest(p)==prov['sha256']))
save('checks/V30-dependency-sources.json',dict(passed=all(x['passed'] for x in rows),records=rows,scope='Fixed remote dependency archives versus local files, allowing CRLF only; excludes unused SIBR viewer and binary wheels.'))
print('EIGEN',count,rows[-1]['passed'],flush=True)
