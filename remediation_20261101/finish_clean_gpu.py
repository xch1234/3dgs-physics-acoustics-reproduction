"""Finish installed-prefix validation after correcting a diagnostic-only API error."""
import json
from common import ROOT,AUDIT,run,runtime_env,save
for name in ('V30-clean-gpu-conda','V30-clean-gpu-torch','V30-clean-gpu-pip','V30-build-diff-gaussian-rasterization','V30-build-simple-knn','V30-clean-gpu-pip-check'):
 assert json.loads((AUDIT/'commands'/f'{name}.json').read_text())['exit_code']==0
prefix='/opt/3dgs-remediation/envs/physgaussian-clean'
run('V30-clean-gpu-imports-corrected',[prefix+'/bin/python','-c','import torch,warp,diff_gaussian_rasterization,simple_knn._C; from importlib.metadata import version; print(torch.__version__,version("warp-lang"))'],env=runtime_env(prefix))
save('checks/V30-clean-gpu-install.json',dict(passed=True,prefix=prefix,scope='Fresh prefix with pinned Conda packages, cached downloads allowed, both CUDA extensions rebuilt; same machine/driver. GPU execution checked separately.',diagnostic_correction='Warp 0.10.1 lacks __version__; query importlib.metadata.version instead. Initial diagnostic failure log retained, no package reinstall or code changes were needed.'))
