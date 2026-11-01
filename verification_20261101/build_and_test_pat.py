import sys
from common import ROOT,AUDIT,run,runtime_env,save
def main():
    prefix='/opt/3dgs-runtime/envs/pat-tools';headers=prefix+'/include'
    project=ROOT/'02_PAT';source=project/'code/ModalSound/ModalSound/src';env=runtime_env('/opt/3dgs-runtime/envs/physgaussian')
    for part in ('modalsound_fem','modalsound_transfer'):(AUDIT/'pat/outputs'/part).mkdir(parents=True,exist_ok=True)
    commands=[('build-pat-fem',['g++','-O2','-std=c++14','-I'+headers,'-I'+str(source),str(project/'code/validate_modalsound_fem.cpp'),str(source/'deformable/stvk.cpp'),str(source/'generic/precision_type.cpp'),'-o',str(AUDIT/'pat/outputs/modalsound_fem/assemble_fem')]),
        ('build-pat-transfer',['g++','-O2','-std=c++14','-I'+headers,'-I'+str(project/'code/dependencies/eigen-git-mirror-3.3.7'),'-I'+str(source),str(project/'code/validate_modalsound_transfer.cpp'),str(source/'generic/precision_type.cpp'),'-L'+prefix+'/lib','-Wl,-rpath,'+prefix+'/lib','-lgsl','-lgslcblas','-o',str(AUDIT/'pat/outputs/modalsound_transfer/evaluate_transfer')])]
    rows=[]
    for name,command in commands:rows.append(run(name,command,env=env,required=False))
    for task in ('fem','transfer','pipeline'):
        rows.append(run('rerun-pat-'+task,[sys.executable,'-u',str(AUDIT/'run_pat_isolated.py'),task],env=env,required=False))
    save('pat-executions.json',rows)
if __name__=='__main__':main()
