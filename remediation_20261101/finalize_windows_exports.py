import json
from common import ROOT,AUDIT,save,digest
records=[]
for project in ('01_PhysGaussian','02_PAT','03_NeuralSound'):
 f=ROOT/project/'docs/environment.yml';s=f.read_text(encoding='utf-8-sig')
 assert '\ufffd' not in s and not any(line.startswith('prefix:') for line in s.splitlines())
 assert s.splitlines()[0].startswith('name: reproduction-')
 records.append(dict(project=project,path=str(f.relative_to(ROOT)),sha256=digest(f)))
assert (ROOT/'02_PAT/docs/environment.yml').read_bytes()==(ROOT/'03_NeuralSound/docs/environment.yml').read_bytes(), 'Do not infer environment identity from names only'
phys=json.loads((AUDIT/'checks/V03-clean-windows-phys.json').read_text());acoustic=json.loads((AUDIT/'checks/V30-clean-cpu.json').read_text());assert phys['passed'] and acoustic['passed']
save('checks/V03.json',dict(passed=True,files=records,acoustics_exports_identical=True,restored_physgaussian_prefix=phys['prefix'],restored_acoustics_prefix=acoustic['prefix'],scope='Portable corrected Windows exports, each distinct specification actually installed from an empty prefix. PhysGaussian CPU-Torch/SH and acoustic PAT pipeline exercised. Linux CUDA is recorded under V30.'))
print('V03 passed: both distinct Windows specifications restored and exercised')
