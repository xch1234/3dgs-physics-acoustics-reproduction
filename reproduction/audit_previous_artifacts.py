"""Compare current content against the 09:19 snapshot; never rewrite manifests."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_EDITS={('03_NeuralSound','code/train_radiation.py'),('03_NeuralSound','code/train_vibration.py')}


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def main():
    results=[];changed=[];missing=[];sources={}
    for project in ('01_PhysGaussian','02_PAT','03_NeuralSound'):
        p=ROOT/project/'docs/artifact-manifest.json'
        sources[project]=dict(manifest_sha256=sha(p),manifest=json.loads(p.read_text(encoding='utf-8')))
        m=sources[project]['manifest']
        for rel,record in m['files'].items():
            actual=ROOT/project/rel
            if not actual.is_file():missing.append([project,rel]);continue
            digest=sha(actual)
            if digest!=record['sha256'] or actual.stat().st_size!=record['bytes']:
                changed.append(dict(project=project,path=rel,expected_sha256=record['sha256'],actual_sha256=digest,authorized_adapter_edit=(project,rel) in EXPECTED_EDITS))
        results.append(dict(project=project,files=len(m['files']),recorded_at=m['recorded_at']))
        print('Compared',project,len(m['files']),'files',flush=True)
    passed=not missing and all(r['authorized_adapter_edit'] for r in changed)
    out=ROOT/'reproduction/audit'
    # Preserve the complete source manifests before later final-manifest refresh.
    (out/'previous-manifests-snapshot.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
    report=dict(time=datetime.now().astimezone().isoformat(),passed=passed,projects=results,missing=missing,changed=changed,
        scope='Bytewise comparison against existing saved manifests; only two explicitly extended training adapters may differ. New experiments are additional files, never replacements for old results.')
    (out/'previous-artifacts-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    assert passed,report
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
