"""Compare all local Ficus assets to the canonical archive linked by the author README."""
import json,hashlib,zipfile,io,argparse
from pathlib import Path
from common import ROOT,AUDIT,save,digest
import gdown,numpy as np
from PIL import Image
parser=argparse.ArgumentParser();parser.add_argument('--file-id',default='18JxhpWD-4ZmuFKLzKlAw-w5PpzZxXOcG');parser.add_argument('--tag',default='');parser.add_argument('--source-label',default='fixed PhysGaussian README / NeRF Synthetic Dataset link');args=parser.parse_args()
url='https://drive.google.com/file/d/'+args.file_id+'/view'
archive=AUDIT/('remote/nerf_synthetic_author'+args.tag+'.zip');rows=[]
try:
 if not archive.exists() or not zipfile.is_zipfile(archive):
  result=gdown.download(id=args.file_id,output=str(archive),quiet=True,resume=True)
  assert result and zipfile.is_zipfile(archive),'Original archive download unavailable or incomplete'
 provenance=json.loads((ROOT/'01_PhysGaussian/docs/ficus-dataset-provenance.json').read_text(encoding='utf8'))
 with zipfile.ZipFile(archive) as z:
  names=z.namelist()
  for item in provenance['files']:
   relative=item['file'].replace('\\','/');matches=[n for n in names if n.endswith('ficus/'+relative)];assert len(matches)==1,(relative,matches)
   data=z.read(matches[0]);sha=hashlib.sha256(data).hexdigest();same=sha==item['sha256'];semantic=same;kind='identical bytes'
   if not same:
    local=ROOT/'01_PhysGaussian/inputs/nerf_synthetic_ficus'/relative
    if relative.endswith('.json'):
     semantic=json.loads(data)==json.loads(local.read_text());kind='parsed JSON'
    elif relative.endswith('.png'):
     with Image.open(io.BytesIO(data)) as a,Image.open(local) as b:semantic=np.array_equal(np.array(a.convert('RGBA')),np.array(b.convert('RGBA')))
     kind='decoded RGBA'
   rows.append(dict(file=relative,archive_entry=matches[0],expected_mirror_sha256=item['sha256'],canonical_sha256=sha,byte_match=same,semantic_match=bool(semantic),comparison=kind))
   if len(rows)%50==0:print('CANONICAL FICUS',len(rows),flush=True)
 report=dict(passed=all(r['semantic_match'] for r in rows),url=url,linked_from=args.source_label,archive_bytes=archive.stat().st_size,archive_sha256=digest(archive),files=len(rows),all_bytes_match=all(r['byte_match'] for r in rows),all_semantics_match=all(r['semantic_match'] for r in rows),rows=rows,scope='Canonical author-linked archive versus all 403 mirror assets; any byte/decoded differences recorded explicitly. Not another-machine execution.')
except Exception as e:
 report=dict(passed=False,url=url,error=repr(e),partial_rows=rows,scope='Failed attempt retained; no original-archive provenance success inferred.')
save('checks/V30-canonical-ficus'+args.tag+'.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ('rows','partial_rows')},indent=2),flush=True)
if not report['passed']:raise SystemExit(1)
