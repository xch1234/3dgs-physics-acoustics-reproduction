"""Sequential original scene runs; each subprocess releases all GPU memory."""
import sys,subprocess,time,json,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCENES={
    'ficus':('ficus_config.json','ficus_whitebg-trained'),
    'bread':('tear_bread_config.json','bread-trained'),
    'pillow2sofa':('pillow2sofa_config.json','pillow2sofa_whitebg-trained'),
    'plane':('plane_config.json','plane-trained'),
    'vasedeck':('vasedeck_config.json','vasedeck_whitebg-trained'),
    'wolf':('wolf_config.json','wolf_whitebg-trained'),
}


def main():
    p=argparse.ArgumentParser();p.add_argument('scenes',nargs='*',default=list(SCENES));args=p.parse_args()
    summary=[]
    for scene in args.scenes:
        config,model=SCENES[scene];tag=f'{scene}_official_full'
        metrics=ROOT/'outputs'/tag/'metrics.json'
        if metrics.exists() and json.loads(metrics.read_text()).get('all_checks_passed'):
            summary.append(dict(scene=scene,status='already verified'));continue
        command=[sys.executable,'-u',str(ROOT/'code/run_official_linux.py'),
            '--model',str(ROOT/'inputs'/model),'--config',str(ROOT/'code/PhysGaussian/config'/config),'--tag',tag]
        logfile=ROOT/'logs'/f'{tag}-suite.log';start=time.perf_counter()
        print('START',scene,flush=True)
        with logfile.open('w') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        row=dict(scene=scene,returncode=result.returncode,elapsed_s=time.perf_counter()-start,
                 status='verified' if result.returncode==0 and metrics.exists() else 'failed',log=str(logfile))
        summary.append(row);print('RESULT',row,flush=True)
        (ROOT/'docs/official-scene-suite.json').write_text(json.dumps(summary,indent=2))
    (ROOT/'docs/official-scene-suite.json').write_text(json.dumps(summary,indent=2))
    if any(row['status']=='failed' for row in summary):raise SystemExit(1)


if __name__=='__main__':main()
