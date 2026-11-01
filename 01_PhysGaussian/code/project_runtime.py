"""Run a project entry with writable runtime caches confined to this project."""
import os
import sys
import runpy
from pathlib import Path

root=Path(__file__).resolve().parents[2]
cache=root/'reproduction/cache'
for key,name in [('CUDA_CACHE_PATH','cuda'),('MPLCONFIGDIR','matplotlib'),('TMPDIR','tmp'),
                 ('TI_OFFLINE_CACHE_FILE_PATH','taichi'),('TRITON_CACHE_DIR','triton')]:
    folder=cache/name;folder.mkdir(parents=True,exist_ok=True);os.environ[key]=str(folder)
os.environ['PYTHONDONTWRITEBYTECODE']='1';sys.dont_write_bytecode=True
import warp as wp
wp.config.kernel_cache_dir=str(cache/'warp')
entry=Path(sys.argv[1]).resolve();entry.relative_to(root)
sys.argv=sys.argv[1:]
sys.path.insert(0,str(entry.parent))
runpy.run_path(str(entry),run_name='__main__')
