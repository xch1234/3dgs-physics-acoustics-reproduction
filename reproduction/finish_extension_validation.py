"""Wait for the active corrected-scene suite, then export and audit new models."""
import argparse,json,subprocess,time
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--wait-pid',required=True,type=int);args=p.parse_args()
    state=dict(started=datetime.now().astimezone().isoformat(),status='waiting for corrected scene suite')
    def save():(ROOT/'reproduction/extension-validation-state.json').write_text(json.dumps(state,indent=2))
    save();process=Path(f'/proc/{args.wait_pid}/cmdline')
    while process.exists():
        try:cmd=process.read_bytes()
        except FileNotFoundError:break
        if b'finish_corrected_scenes.py' not in cmd:break
        time.sleep(5)
    for scene in ('bread','plane','vasedeck'):
        m=json.loads((ROOT/f'01_PhysGaussian/outputs/{scene}_sh_corrected/metrics.json').read_text())
        assert m['all_checks_passed'] and m['sh_frame_correction']
    state['status']='new predictions, four checkpoint audits, eleven-scene summary and extension reports';save()
    with (ROOT/'reproduction/extension-validation-stages.log').open('w') as log:
        result=subprocess.run(['bash','--noprofile','--norc',str(ROOT/'reproduction/run_scope_extensions.sh'),'validation-only'],stdout=log,stderr=subprocess.STDOUT)
    state['exit_code']=result.returncode;state['status']='completed' if result.returncode==0 else 'failed';save()
    raise SystemExit(result.returncode)


if __name__=='__main__':main()
