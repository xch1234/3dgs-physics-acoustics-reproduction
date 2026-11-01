"""Invoke reviewed existing numerical routines, redirecting only their I/O roots."""
import sys,importlib,os
from common import ROOT,AUDIT,save,digest
def main():
    task=sys.argv[1];sys.path.insert(0,str(ROOT/'02_PAT/code'))
    name={'fem':'run_modalsound_fem','transfer':'run_modalsound_transfer','pipeline':'run_pat'}[task]
    module=importlib.import_module(name)
    isolated=AUDIT/'pat';isolated.mkdir(exist_ok=True)
    for part in ('docs','inputs','outputs','outputs/modalsound_fem','outputs/modalsound_transfer'):(isolated/part).mkdir(parents=True,exist_ok=True)
    code=isolated/'code'
    if not code.exists():code.symlink_to(ROOT/'02_PAT/code',target_is_directory=True)
    module.ROOT=isolated
    if task=='pipeline':
        module.OUT=isolated/'outputs/pat_pipeline';module.FEM=ROOT/'02_PAT/inputs/official_fem_result.npz'
    save('io-redirection-'+task+'.json',dict(source=str(ROOT/'02_PAT/code'/f'{name}.py'),sha256=digest(ROOT/'02_PAT/code'/f'{name}.py'),redirected_ROOT=str(isolated),method='Unmodified imported numerical functions; change module ROOT/OUT/FEM globals only to isolate generated files. Original source is not edited.'))
    module.main()
if __name__=='__main__':main()
