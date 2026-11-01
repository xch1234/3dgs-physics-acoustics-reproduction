"""Remaining checks scheduled after the current GPU follow-up process finishes."""
import sys,time,json,shutil
from common import ROOT,AUDIT,run,runtime_env,save,digest
def main():
    while True:
        path=AUDIT/'followup-state.json'
        if path.exists() and json.loads(path.read_text())['status']=='completed':break
        if (AUDIT/'3dgs-state.json').exists() and json.loads((AUDIT/'3dgs-state.json').read_text())['status']=='failed':raise RuntimeError('Fresh 3DGS prerequisite failed')
        time.sleep(5)
    phys='/opt/3dgs-runtime/envs/physgaussian';neural='/opt/3dgs-runtime/envs/neuralsound';rows=[]
    for name,script,prefix in [('vibration-fresh-solves','vibration_rerun.py',neural),('cuda-source-build','build_cuda.py',phys),('checkpoints-readback','checkpoint_readback.py',neural)]:
        if (AUDIT/'commands'/f'{name}.json').exists():continue
        rows.append(run(name,[prefix+'/bin/python','-u',str(AUDIT/script)],env=runtime_env(prefix),required=False));save('late-checks-state.json',dict(status=name,stages=rows))
    old=ROOT/'01_PhysGaussian/outputs/ficus_reconstruction';new=AUDIT/'outputs/ficus_existing_rerender';new.mkdir()
    shutil.copy2(old/'cfg_args',new/'cfg_args');(new/'point_cloud/iteration_30000').mkdir(parents=True)
    shutil.copy2(old/'point_cloud/iteration_30000/point_cloud.ply',new/'point_cloud/iteration_30000/point_cloud.ply')
    repo=ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting';env=runtime_env(phys)
    rows.append(run('3dgs-existing-model-rerender',[phys+'/bin/python',str(repo/'render.py'),'-m',str(new),'-s',str(ROOT/'01_PhysGaussian/inputs/nerf_synthetic_ficus'),'--eval','--white_background','--data_device','cpu','--resolution','1','--iteration','30000','--skip_train'],cwd=repo,env=env,required=False))
    if rows[-1]['exit_code']==0:
        rows.append(run('3dgs-evaluate-existing-rerender',[phys+'/bin/python',str(AUDIT/'evaluate_3dgs.py'),'--model',str(new),'--tag','existing_model_rerender'],env=env,required=False))
        import numpy as np
        from PIL import Image
        deltas=[]
        for p in sorted((old/'test/ours_30000/renders').glob('*.png')):
            a=np.array(Image.open(p)).astype(float);b=np.array(Image.open(new/'test/ours_30000/renders'/p.name)).astype(float);deltas.append(float(abs(a-b).max()))
        save('checks/existing-model-rerender.json',dict(images=len(deltas),max_byte_difference=max(deltas),identical_images=sum(x==0 for x in deltas),model_sha256=digest(new/'point_cloud/iteration_30000/point_cloud.ply')))
    save('late-checks-state.json',dict(status='completed',stages=rows))
if __name__=='__main__':main()
