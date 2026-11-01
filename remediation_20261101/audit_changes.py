"""Syntax, source-boundary and reversible local-change documentation."""
from common import ROOT,AUDIT,save,digest
import ast,difflib,tarfile,json
from pathlib import Path
files=list(AUDIT.glob('*.py'))
files += [ROOT/p for p in ['01_PhysGaussian/code/snow_adapter.py','01_PhysGaussian/code/run_official_linux.py','01_PhysGaussian/code/run_scene_suite.py','02_PAT/code/phase_audio.py','02_PAT/code/bem_near_quadrature.py','03_NeuralSound/code/train_radiation.py','03_NeuralSound/code/run_neural_audio.py']]
syntax=[]
for f in files:
 ast.parse(f.read_text(encoding='utf-8-sig'),filename=str(f));syntax.append(dict(file=str(f.relative_to(ROOT)),sha256=digest(f)))
sources=[]
for project,name in [('01_PhysGaussian','PhysGaussian'),('02_PAT','ModalSound'),('03_NeuralSound','NeuralSound')]:
 errors=[];count=0
 with tarfile.open(AUDIT/'remote'/f'{name}.tar.gz') as tar:
  for member in tar:
   if not member.isfile():continue
   rel='/'.join(member.name.split('/')[1:]);f=ROOT/project/'code'/name/rel
   a=tar.extractfile(member).read().replace(b'\r\n',b'\n');b=f.read_bytes().replace(b'\r\n',b'\n');count+=1
   if a!=b:errors.append(rel)
 assert not errors,(name,errors);sources.append(dict(repo=name,files=count,substantive_changes=errors))
diffs=[];backups=[]
for f in (AUDIT/'backups').rglob('*'):
 if not f.is_file():continue
 rel=f.relative_to(AUDIT/'backups');target=ROOT/rel
 if not target.exists():
  # Environment backups are stored at <project>/environment.yml.
  if f.name=='environment.yml':target=ROOT/rel.parent/'docs/environment.yml'
 if not target.exists():backups.append(dict(backup=str(f.relative_to(AUDIT)),target='not inferred'));continue
 old=f.read_text(encoding='utf-8-sig');new=target.read_text(encoding='utf-8-sig')
 diffs.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='before/'+str(target.relative_to(ROOT)),tofile='after/'+str(target.relative_to(ROOT))))
 backups.append(dict(backup=str(f.relative_to(AUDIT)),current=str(target.relative_to(ROOT)),before_sha256=digest(f),after_sha256=digest(target)))
(AUDIT/'local_changes.patch').write_text(''.join(diffs),encoding='utf8')
runtime_alias=Path('/opt/3dgs-runtime/PhysGaussian-source');runtime=None
if runtime_alias.exists():
 assert runtime_alias.resolve()==(ROOT/'01_PhysGaussian/code/PhysGaussian').resolve()
 runtime=dict(alias=str(runtime_alias),resolved=str(runtime_alias.resolve()),matches_verified_source=True,kernels={name:digest(runtime_alias/'mpm_solver_warp'/name) for name in ['mpm_utils.py','engine_utils.py','warp_utils.py','mpm_solver_warp.py']})
save('checks/source-and-syntax.json',dict(passed=True,parsed=syntax,upstream=sources,backups=backups,runtime_source_alias=runtime,scope='Syntax and source boundaries only; successful runtime checks remain separate.'))
print('PARSED',len(syntax),'UPSTREAM UNCHANGED',sources,flush=True)

