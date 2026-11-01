"""Run every released scene with nonidentity preprocessing rotation after the active queue."""
import os,sys,json,time,subprocess,argparse
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--wait-pid',required=True,type=int);args=p.parse_args()
    state=dict(started=datetime.now().astimezone().isoformat(),status='waiting for active anisotropy queue',stages=[])
    def save():(ROOT/'reproduction/sh-correction-state.json').write_text(json.dumps(state,indent=2))
    save();process=Path(f'/proc/{args.wait_pid}/cmdline')
    while process.exists():
        try:cmd=process.read_bytes()
        except FileNotFoundError:break
        if b'finish_scope_extensions.py' not in cmd:break
        time.sleep(5)
    assert json.loads((ROOT/'01_PhysGaussian/docs/anisotropy-metrics.json').read_text())['all_checks_passed']
    project=ROOT/'01_PhysGaussian'
    env=os.environ.copy();env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',
        PHYSGAUSSIAN_SOURCE='/opt/3dgs-runtime/PhysGaussian-source',
        LD_LIBRARY_PATH='/usr/lib/wsl/lib:/opt/3dgs-runtime/envs/physgaussian/lib',
        PATH='/opt/3dgs-runtime/envs/physgaussian/bin:'+env['PATH'])
    # Use exact model/config paths already recorded by the original full runs.
    for name in ('bread','plane','vasedeck'):
        tag=f'{name}_sh_corrected';out=project/'outputs'/tag
        if (out/'metrics.json').exists() and json.loads((out/'metrics.json').read_text()).get('all_checks_passed'):
            state['stages'].append(dict(scene=name,status='existing completed artifact'));save();continue
        original=json.loads((project/'outputs'/f'{name}_official_full'/'metrics.json').read_text())
        model=Path(original['model_checkpoint']).parents[2]
        config=project/'outputs'/f'{name}_official_full'/'config.json'
        state['status']=tag;save();start=time.perf_counter()
        command=[sys.executable,'-u',str(project/'code/project_runtime.py'),str(project/'code/run_official_linux.py'),
            '--model',str(model),'--config',str(config),'--tag',tag,'--correct-sh-frame']
        with (project/'logs'/f'{tag}.log').open('w') as log:
            result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
        row=dict(scene=name,exit_code=result.returncode,elapsed_s=time.perf_counter()-start);state['stages'].append(row)
        if result.returncode:state['status']='failed';save();raise SystemExit(result.returncode)
        metrics=json.loads((out/'metrics.json').read_text())
        assert metrics['all_checks_passed'] and metrics['sh_frame_correction']
        assert metrics['rendered_frames']==original['rendered_frames'] and metrics['model_sha256']==original['model_sha256']
        row['status']='completed and checked';save()
    state['status']='completed';save()


if __name__=='__main__':main()
