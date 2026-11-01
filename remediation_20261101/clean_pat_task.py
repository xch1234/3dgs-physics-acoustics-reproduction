"""Compile PAT tools from a fresh Conda prefix after GPU jobs release RAM."""
import sys,time,importlib
from pathlib import Path
from common import ROOT,AUDIT,run,runtime_env,save,digest
def isolated(task):
 sys.path.insert(0,str(ROOT/'02_PAT/code'))
 module=importlib.import_module({'fem':'run_modalsound_fem','transfer':'run_modalsound_transfer'}[task])
 isolated=AUDIT/'pat_clean'
 for part in ('docs','inputs','outputs','outputs/modalsound_fem','outputs/modalsound_transfer'):(isolated/part).mkdir(parents=True,exist_ok=True)
 code=isolated/'code'
 if not code.exists():code.symlink_to(ROOT/'02_PAT/code',target_is_directory=True)
 module.ROOT=isolated
 save('checks/V30-pat-io-'+task+'.json',dict(source=str(Path(module.__file__)),sha256=digest(module.__file__),redirected_ROOT=str(isolated),method='Original imported numerical routine with isolated ROOT; no source edit.'))
 module.main()
def main():
 while not (AUDIT/'unified-neural-complete.json').exists():time.sleep(10)
 prefix='/opt/3dgs-remediation/envs/pat-tools-clean';assert not Path(prefix).exists(),'Must start with empty Conda prefix'
 env=runtime_env();env['CONDA_PKGS_DIRS']='/opt/3dgs-runtime/pkgs'
 rows=[run('V30-pat-clean-conda',['/opt/3dgs-runtime/miniconda3/bin/conda','create','--yes','--prefix',prefix,'--file',ROOT/'02_PAT/docs/conda-explicit-linux64.txt'],env=env)]
 source=ROOT/'02_PAT/code/ModalSound/ModalSound/src';project=ROOT/'02_PAT'
 out=AUDIT/'pat_clean/outputs'
 for part in ('modalsound_fem','modalsound_transfer'):(out/part).mkdir(parents=True,exist_ok=True)
 commands=[('fem',['g++','-O2','-std=c++14','-I'+prefix+'/include','-I'+str(source),str(project/'code/validate_modalsound_fem.cpp'),str(source/'deformable/stvk.cpp'),str(source/'generic/precision_type.cpp'),'-o',str(out/'modalsound_fem/assemble_fem')]),
 ('transfer',['g++','-O2','-std=c++14','-I'+prefix+'/include','-I'+str(project/'code/dependencies/eigen-git-mirror-3.3.7'),'-I'+str(source),str(project/'code/validate_modalsound_transfer.cpp'),str(source/'generic/precision_type.cpp'),'-L'+prefix+'/lib','-Wl,-rpath,'+prefix+'/lib','-lgsl','-lgslcblas','-o',str(out/'modalsound_transfer/evaluate_transfer')])]
 for task,command in commands:
  r=run('V30-pat-clean-build-'+task,command,env=env,required=False);rows.append(r)
  if r['exit_code']==0:rows.append(run('V30-pat-clean-test-'+task,['/opt/3dgs-remediation/envs/physgaussian-clean/bin/python','-u',__file__,task],env=env,required=False))
 save('checks/V30-clean-pat-execution.json',dict(passed=len(rows)==5 and all(r['exit_code']==0 for r in rows),prefix=prefix,commands=rows,scope='Fresh Conda GSL/Boost + rebuilt original C++ FEM/transfer components, independent numerical reference in fresh PhysGaussian Python. System GCC and same machine; not original PAT full GUI/FastBEM.'))
 save('clean-pat-complete.json',dict(failed=[r['name'] for r in rows if r['exit_code']!=0]))
if __name__=='__main__':
 if len(sys.argv)>1:isolated(sys.argv[1])
 else:main()
