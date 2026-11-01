"""Wait for the currently live paper-schedule trainer, then run anisotropy."""
import argparse,json,subprocess,time
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--wait-pid',required=True,type=int);args=p.parse_args()
    state=dict(started=datetime.now().astimezone().isoformat(),status='waiting for live radiation paper-schedule training',wait_pid=args.wait_pid)
    def save():(ROOT/'reproduction/scope-extensions-state.json').write_text(json.dumps(state,indent=2))
    save();process=Path(f'/proc/{args.wait_pid}/cmdline')
    while process.exists():
        try:cmd=process.read_bytes()
        except FileNotFoundError:break
        if b'train_radiation.py' not in cmd or b'--paper-schedule' not in cmd:break
        time.sleep(5)
    rad=ROOT/'03_NeuralSound/outputs/radiation_paper_schedule/metrics.json'
    assert rad.exists() and json.loads(rad.read_text())['training_completed'],'Paper-schedule stage did not finish; inspect its log.'
    state['status']='anisotropy reconstruction and full simulation';save()
    with (ROOT/'01_PhysGaussian/logs/ficus-anisotropy-pipeline.log').open('w') as log:
        result=subprocess.run(['bash','--noprofile','--norc',str(ROOT/'01_PhysGaussian/code/run_anisotropy.sh')],stdout=log,stderr=subprocess.STDOUT)
    state['exit_code']=result.returncode
    state['status']='completed' if result.returncode==0 else 'failed; inspect anisotropy pipeline log';save()
    if result.returncode:raise SystemExit(result.returncode)
    assert json.loads((ROOT/'01_PhysGaussian/docs/anisotropy-metrics.json').read_text())['all_checks_passed']


if __name__=='__main__':main()
