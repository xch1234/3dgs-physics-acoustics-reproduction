"""Sequential isolated full upstream training/render/evaluation validation."""
import sys,shutil,json
from pathlib import Path
from common import ROOT,AUDIT,run,runtime_env,save
PREFIX='/opt/3dgs-runtime/envs/physgaussian'
def main():
    env=runtime_env(PREFIX);repo=ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting'
    source=ROOT/'01_PhysGaussian/inputs/nerf_synthetic_ficus';out=AUDIT/'outputs/ficus_fresh_30000'
    assert not out.exists(),'Never overwrite a previous validation run'
    assert (source/'points3d.ply').is_file(),'Refuse dataset-side initialization writes'
    cache=AUDIT/'cache/torch/hub/checkpoints';cache.mkdir(parents=True,exist_ok=True)
    for name in ('vgg.pth','vgg16-397923af.pth'):
        shutil.copy2(Path('/opt/3dgs-runtime/torch-cache/hub/checkpoints')/name,cache/name)
    state=dict(status='training',stages=[]);save('3dgs-state.json',state)
    stages=[('3dgs-train',[sys.executable,'-u',str(repo/'train.py'),'-s',str(source),'-m',str(out),'--eval','--white_background','--data_device','cpu','--resolution','1','--iterations','30000','--port','6031','--test_iterations','30000','--save_iterations','7000','15000','30000','--checkpoint_iterations','7000','15000','30000']),
        ('3dgs-render',[sys.executable,'-u',str(repo/'render.py'),'-m',str(out),'-s',str(source),'--eval','--white_background','--data_device','cpu','--resolution','1','--iteration','30000','--skip_train']),
        ('3dgs-evaluate-fresh',[sys.executable,'-u',str(AUDIT/'evaluate_3dgs.py'),'--model',str(out),'--tag','fresh_30000']),
        ('3dgs-evaluate-existing',[sys.executable,'-u',str(AUDIT/'evaluate_3dgs.py'),'--model',str(ROOT/'01_PhysGaussian/outputs/ficus_reconstruction'),'--tag','existing_baseline'])]
    for name,command in stages:
        state['status']=name;save('3dgs-state.json',state)
        row=run(name,command,cwd=repo,env=env,required=False);state['stages'].append(row)
        if row['exit_code']!=0:
            state['status']='failed';save('3dgs-state.json',state);raise SystemExit(1)
    state['status']='completed';save('3dgs-state.json',state)
if __name__=='__main__':main()
