"""Download the five remaining author-provided models, retain input provenance."""
import json
import hashlib
import zipfile
from pathlib import Path
import gdown

ROOT=Path(__file__).resolve().parents[1]


def main():
    inventory=json.loads((ROOT/'docs/official-model-inventory.json').read_text())
    records=[]
    for item in inventory:
        archive=ROOT/'outputs'/item['path']
        if not archive.exists() or not zipfile.is_zipfile(archive):
            result=gdown.download(id=item['id'],output=str(archive),resume=True)
            if result is None: raise RuntimeError(item)
        extracted=[]
        with zipfile.ZipFile(archive) as z:
            for entry in z.infolist():
                name=entry.filename
                if not (('/point_cloud/iteration_' in name and name.endswith('/point_cloud.ply')) or
                        name.endswith('/cameras.json') or name.endswith('/cfg_args')): continue
                dest=(ROOT/'inputs'/name).resolve()
                if not dest.is_relative_to((ROOT/'inputs').resolve()): raise ValueError(name)
                dest.parent.mkdir(parents=True,exist_ok=True)
                if not dest.exists() or dest.stat().st_size != entry.file_size:
                    with z.open(entry) as source, dest.open('wb') as target:
                        while chunk:=source.read(1024*1024): target.write(chunk)
                h=hashlib.sha256()
                with dest.open('rb') as f:
                    for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
                extracted.append(dict(path=str(dest.relative_to(ROOT)),bytes=dest.stat().st_size,sha256=h.hexdigest()))
        assert any(r['path'].endswith('.ply') for r in extracted),item
        records.append(dict(**item,archive_bytes=archive.stat().st_size,files=extracted))
        (ROOT/'docs/official-model-downloads.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        print('COMPLETE',item['path'],len(extracted),'input files',flush=True)


if __name__=='__main__':main()
