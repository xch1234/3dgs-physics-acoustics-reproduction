"""Unchanged constitutive tests in Linux; omit only the Windows include-path shim."""
import sys
from common import ROOT,AUDIT,save
leaf='/opt/3dgs-runtime/PhysGaussian-source/mpm_solver_warp'
sys.path[:0]=[leaf,str(ROOT/'01_PhysGaussian/code')]
# Preload the real released leaf modules via the existing ASCII source alias.
import warp_utils,mpm_utils,engine_utils,mpm_solver_warp
import validate_materials as m
import warp as wp
wp.config.kernel_cache_dir=str(AUDIT/'cache/warp_materials_linux')
m.ROOT=AUDIT/'materials_linux'
(m.ROOT/'outputs').mkdir(parents=True,exist_ok=True)
(m.ROOT/'docs').mkdir(exist_ok=True)
m.enable=lambda:None
save('materials_linux/adapter.json',dict(scope='Existing validate_materials numeric functions unchanged; Windows-only include-path hook omitted on Linux; only output/cache and module import paths redirected',modules={k:sys.modules[k].__file__ for k in ('warp_utils','mpm_utils','engine_utils','mpm_solver_warp')}))
m.main()
