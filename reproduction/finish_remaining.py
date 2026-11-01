"""Operational queue: finish the live Wolf run, reconstruction, then simulation.

Uses existing scientific entry points without changing their configurations.
Stops on any failure; never marks a missing result as completed.
"""
import argparse
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--wait-pid',type=int,required=True)
    args=parser.parse_args()
    state=dict(started=datetime.now().astimezone().isoformat(),status='waiting for active Wolf worker',stages=[])
    def save():
        (ROOT/'reproduction/remaining-pipeline-state.json').write_text(json.dumps(state,indent=2))
    save()
    process=Path(f'/proc/{args.wait_pid}/cmdline')
    while process.exists():
        try:command=process.read_bytes()
        except FileNotFoundError:break
        if b'run_official_linux.py' not in command or b'wolf' not in command:break
        time.sleep(5)
    wolf=json.loads((ROOT/'01_PhysGaussian/outputs/wolf_official_full/metrics.json').read_text())
    assert wolf['all_checks_passed'] and wolf['rendered_frames']==50
    for name,script,tag,logfile in (
        ('reconstruction','run_reconstruction.sh','ficus_reconstruction','ficus-reconstruction-pipeline.log'),
        ('new-model simulation','run_reconstructed_simulation.sh','ficus_reconstructed_full','ficus-reconstructed-full.log'),
    ):
        metrics=ROOT/'01_PhysGaussian/outputs'/tag/'metrics.json'
        if metrics.exists() and json.loads(metrics.read_text()).get('all_checks_passed'):
            state['stages'].append(dict(stage=name,status='existing completed artifact'))
            save();continue
        state['status']=name;save();print('START',name,flush=True)
        start=time.perf_counter()
        with (ROOT/'01_PhysGaussian/logs'/logfile).open('w') as log:
            result=subprocess.run(['bash','--noprofile','--norc',str(ROOT/'01_PhysGaussian/code'/script)],stdout=log,stderr=subprocess.STDOUT)
        row=dict(stage=name,exit_code=result.returncode,elapsed_s=time.perf_counter()-start,log=logfile)
        state['stages'].append(row)
        if result.returncode!=0 or not metrics.exists():
            state['status']='failed; inspect stage log';save();raise SystemExit(1)
        assert json.loads(metrics.read_text())['all_checks_passed']
        row['status']='completed and checked';save();print(row,flush=True)
    state['status']='all remaining scientific stages completed';save()


if __name__=='__main__':main()
