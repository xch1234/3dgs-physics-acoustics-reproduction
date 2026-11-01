"""Named isolated Linux command, usable through wsl without shell expansion."""
import sys
from common import ROOT,AUDIT,run,runtime_env
name,prefix,script,*args=sys.argv[1:]
env=runtime_env(prefix);env['TORCH_HOME']='/opt/3dgs-runtime/torch-cache';env['TMPDIR']='/opt/3dgs-runtime/tmp'
row=run(name,[prefix+'/bin/python','-u',script,*args],env=env,required=False)
raise SystemExit(row['exit_code'] or (1 if row.get('error') else 0))
