from pathlib import Path
import requests,hashlib,json,concurrent.futures,tarfile,io,subprocess,time
R=Path(__file__).resolve().parents[1];A=R/'remediation_20261101';out=A/'remote';out.mkdir(exist_ok=True);records=[]
repos=[('01_PhysGaussian/code/PhysGaussian','XPandora/PhysGaussian','8339ed6aa2cd5d50e1001a254a3d95aea678a956'),('02_PAT/code/ModalSound','cxzheng/ModalSound','1af5e40893d0ad1b73b594a0cba7a5466b4fc56d'),('03_NeuralSound/code/NeuralSound','hellojxt/NeuralSound','b18e81b1e3dba7e963b09a7d9a45b584707d805f')]
for local,repo,commit in repos:
 url=f'https://api.github.com/repos/{repo}/tarball/{commit}';r=requests.get(url,timeout=120);r.raise_for_status();blob=r.content;(out/(repo.split('/')[-1]+'.tar.gz')).write_bytes(blob);errors=[];count=0
 with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
  for m in tar.getmembers():
   if not m.isfile():continue
   rel='/'.join(m.name.split('/')[1:]);p=R/local/rel
   if not p.is_file():errors.append({'file':rel,'reason':'missing local'});continue
   b=tar.extractfile(m).read();a=p.read_bytes();count+=1
   if a!=b and a.replace(b'\r\n',b'\n')!=b.replace(b'\r\n',b'\n'):errors.append({'file':rel,'reason':'semantic bytes differ'})
 record={'repo':repo,'commit':commit,'url':url,'archive_sha256':hashlib.sha256(blob).hexdigest(),'files_checked':count,'differences':errors};records.append(record);print(repo,count,'differences',len(errors),flush=True)
prov=json.loads((R/'01_PhysGaussian/docs/ficus-dataset-provenance.json').read_text(encoding='utf8'))
def check(f):
 for trial in range(3):
  try:
   rr=requests.get(f['url'],timeout=90);rr.raise_for_status();sha=hashlib.sha256(rr.content).hexdigest();return {'file':f['file'],'bytes':len(rr.content),'expected':f['sha256'],'remote_sha256':sha,'match':sha==f['sha256']}
  except requests.RequestException as e:
   if trial==2:return {'file':f['file'],'error':str(e)}
   time.sleep(2)
files=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for f in pool.map(check,prov['files']):
  files.append(f)
  if len(files)%50==0:print('REMOTE FICUS',len(files),flush=True)
result={'upstream_source':records,'ficus_files':files,'all_sources_match':all(not x['differences'] for x in records),'all_mirror_files_match':all(f.get('match',False) for f in files),'scope':'author GitHub fixed commits and pinned public mirror fetched again via HTTPS; does not authenticate mirror to original author Drive hash, and does not cover all official pretrained weights'}
(A/'checks/V30-remote.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('REMOTE DONE',result['all_sources_match'],result['all_mirror_files_match'])
# Save current author dataset/reference pages, not fabricated availability claims.
pages=[('PhysGaussian','https://xpandora.github.io/PhysGaussian/'),('NeuralSound','https://hellojxt.github.io/NeuralSound/'),('ABC','https://deep-geometry.github.io/abc-dataset/')];pages_out=[]
for name,url in pages:
 try:
  r=requests.get(url,timeout=60);(out/(name+'.html')).write_text(r.text,encoding='utf8');pages_out.append({'name':name,'url':url,'status':r.status_code,'bytes':len(r.content)})
 except requests.RequestException as e:pages_out.append({'name':name,'url':url,'error':str(e)})
(A/'checks/V29-resource-access.json').write_text(json.dumps(pages_out,indent=2));print(pages_out,flush=True)
