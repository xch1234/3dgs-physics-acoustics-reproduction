import json,sys
from common import ROOT,AUDIT,save,run,runtime_env
def main():
    before=json.loads((AUDIT/'original-files-before.json').read_text(encoding='utf-8'));rows=[]
    for project in ('01_PhysGaussian','02_PAT','03_NeuralSound'):
        manifest=json.loads((ROOT/project/'docs/artifact-manifest.json').read_text());bad=[]
        for name,row in manifest['files'].items():
            current=before.get(project+'/'+name)
            if current!=row:bad.append(dict(file=name,recorded=row,current=current))
        rows.append(dict(project=project,files=len(manifest['files']),mismatches=bad))
    config=[]
    for folder in ('01_PhysGaussian','02_PAT','03_NeuralSound'):
        for p in (ROOT/folder/'docs').glob('environment*.yml'):
            raw=p.read_text(encoding='utf-8-sig');bad=[line for line in raw.splitlines() if '\ufffd' in line]
            config.append(dict(path=p.relative_to(ROOT).as_posix(),unicode_replacement_lines=bad))
    save('checks/manifest-comparison.json',dict(records=rows,passed=all(not r['mismatches'] for r in rows),note='Compared file bytes captured independently this turn against old manifest values; did not trust old pass flags or regenerate manifests.'))
    save('checks/environment-export-text.json',config)
    print(json.dumps(dict(manifests=[dict(project=r['project'],files=r['files'],mismatches=len(r['mismatches'])) for r in rows],environment_exports_with_replacement_chars=sum(bool(r['unicode_replacement_lines']) for r in config)),ensure_ascii=False))
if __name__=='__main__':main()
