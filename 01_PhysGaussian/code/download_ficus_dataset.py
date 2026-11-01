"""Download a pinned public mirror of NeRF synthetic Ficus RGB(A) and cameras.

Retain source provenance and hashes; do not claim author-hosted hash identity.
"""
import concurrent.futures,hashlib,json,re,time
from pathlib import Path
import requests
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
REPO='pablovela5620/nerf-synthetic-mirror'
REV='23e7eaa65ff836405329c7b6b4a34afaeb3a70e2'


def main():
    out=ROOT/'inputs/nerf_synthetic_ficus';out.mkdir(parents=True,exist_ok=True)
    response=requests.get(f'https://huggingface.co/api/datasets/{REPO}/revision/{REV}',timeout=60);response.raise_for_status()
    data=response.json();assert data['sha']==REV
    names=[s['rfilename'] for s in data['siblings'] if re.fullmatch(r'ficus/((train|test|val)/r_\d+\.png|transforms_(train|test|val)\.json)',s['rfilename'])]
    assert len(names)>=303,len(names)
    def download(name):
        target=out/name.removeprefix('ficus/');target.parent.mkdir(parents=True,exist_ok=True)
        url=f'https://huggingface.co/datasets/{REPO}/resolve/{REV}/{name}'
        if not target.exists():
            for attempt in range(4):
                try:
                    r=requests.get(url,timeout=60);r.raise_for_status()
                    part=target.with_suffix(target.suffix+'.part');part.write_bytes(r.content);part.replace(target);break
                except requests.RequestException:
                    if attempt==3:raise
                    time.sleep(2)
        if target.suffix=='.png':
            with Image.open(target) as im:
                assert im.size==(800,800) and im.mode=='RGBA',(name,im.size,im.mode)
                im.verify()
        else:assert 'frames' in json.loads(target.read_text())
        return dict(file=str(target.relative_to(out)),bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),url=url)
    records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for record in pool.map(download,names):
            records.append(record)
            if len(records)%20==0:print('DOWNLOADED',len(records),'/',len(names),flush=True)
    counts={}
    for phase in ('train','test','val'):
        meta=json.loads((out/f'transforms_{phase}.json').read_text())
        counts[phase]=len(meta['frames'])
        for frame in meta['frames']:
            relative=frame['file_path'].removeprefix('./')+'.png'
            assert re.fullmatch(r'(train|test|val)/r_\d+\.png',relative),relative
            assert (out/relative).exists()
    result=dict(source_mirror=REPO,revision=REV,original_dataset_project='https://github.com/bmild/nerf',
        original_dataset_folder='https://drive.google.com/drive/folders/1cK3UDIJqKAAm7zyrxRYVFJ0BRMgrwhh4',
        source_note='public mirror, pinned commit and local hashes; no author hash manifest available',
        all_images_verified=True,frame_counts=counts,files=records)
    (ROOT/'docs/ficus-dataset-provenance.json').write_text(json.dumps(result,indent=2))
    print('COMPLETE',counts,flush=True)


if __name__=='__main__':main()
