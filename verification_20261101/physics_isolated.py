"""Re-run reviewed published physics routines with isolated output roots."""
import sys,os,importlib
from pathlib import Path
from common import ROOT,AUDIT,save,digest
def main():
    task=sys.argv[1];code=ROOT/'01_PhysGaussian/code';sys.path.insert(0,str(code))
    isolated=AUDIT/'physics';(isolated/'outputs').mkdir(parents=True,exist_ok=True);(isolated/'docs').mkdir(exist_ok=True)
    os.environ['PHYSGAUSSIAN_SOURCE']='/opt/3dgs-runtime/PhysGaussian-source'
    if task=='sh':
        m=importlib.import_module('validate_sh_frame');m.ROOT=isolated;m.main();return
    import warp as wp
    wp.config.kernel_cache_dir=str(AUDIT/'cache/warp')
    if task=='transport':
        m=importlib.import_module('validate_gaussian_transport');m.ROOT=isolated
        wp.config.kernel_cache_dir=str(AUDIT/'cache/warp');m.main();return
    if task=='simulation':
        m=importlib.import_module('run_official_linux');m.ROOT=isolated
        sys.argv=[str(code/'run_official_linux.py'),'--model',str(AUDIT/'outputs/ficus_fresh_30000'),'--config',str(ROOT/'01_PhysGaussian/code/PhysGaussian/config/ficus_config.json'),'--tag','ficus_fresh_full']
        save('physics/io-redirection.json',dict(adapter_sha256=digest(code/'run_official_linux.py'),ROOT=str(isolated),model=str(AUDIT/'outputs/ficus_fresh_30000'),scope='Existing adapter unchanged except output root; full original 125-frame Ficus config and original gs_simulation'))
        m.main();return
    raise ValueError(task)
if __name__=='__main__':main()
