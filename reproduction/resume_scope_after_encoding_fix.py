"""Resume completed model after a preserved Warp source-path encoding failure."""
import json,subprocess,sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    state=dict(started=datetime.now().astimezone().isoformat(),status='resuming',stages=[])
    def save():(ROOT/'reproduction/scope-resume-state.json').write_text(json.dumps(state,indent=2))
    stages=[('anisotropy simulation',['bash','--noprofile','--norc',str(ROOT/'01_PhysGaussian/code/run_anisotropy.sh'),'--simulation-only']),
        ('corrected SH scenes',[sys.executable,'-u',str(ROOT/'reproduction/finish_corrected_scenes.py'),'--wait-pid','0']),
        ('extension validation',['bash','--noprofile','--norc',str(ROOT/'reproduction/run_scope_extensions.sh'),'validation-only'])]
    for name,command in stages:
        state['status']=name;save();print('START',name,flush=True)
        result=subprocess.run(command)
        state['stages'].append(dict(name=name,exit_code=result.returncode))
        if result.returncode:
            state['status']='failed';save();raise SystemExit(result.returncode)
        save()
    state['status']='completed';save()


if __name__=='__main__':main()
