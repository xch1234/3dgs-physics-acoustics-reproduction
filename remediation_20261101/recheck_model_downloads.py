import json,sys,hashlib,zipfile
from common import ROOT,AUDIT,run,save,digest
import gdown
rows=[];dest=AUDIT/'remote/models';dest.mkdir(parents=True,exist_ok=True)
for entry in json.loads((ROOT/'01_PhysGaussian/docs/official-model-downloads.json').read_text()):
 row=dict(id=entry['id'],archive=entry['path'],files=[])
 try:
  archive=dest/entry['path'];gdown.download(id=entry['id'],output=str(archive),quiet=True,resume=True)
  row['archive_sha256']=digest(archive)
  with zipfile.ZipFile(archive) as z:
   for f in entry['files']:
    path=f['path'].replace('\\','/');name=path.removeprefix('inputs/')
    sha=hashlib.sha256(z.read(name)).hexdigest();row['files'].append(dict(file=name,expected=f['sha256'],remote_sha256=sha,match=sha==f['sha256']))
  row['passed']=all(f['match'] for f in row['files'])
 except Exception as e:row.update(passed=False,error=repr(e))
 rows.append(row);save('checks/V30-remote-models.json',dict(rows=rows,passed=all(r['passed'] for r in rows),scope='New download from the recorded author Google Drive IDs, checked against all recorded cfg/camera/PLY contents; no author-signed checksums'))
 print(entry['path'],row['passed'],flush=True)
