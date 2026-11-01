"""Recompile copies of pinned CUDA extensions without installing or editing originals."""
import sys,shutil,json
from pathlib import Path
from common import ROOT,AUDIT,run,runtime_env,save,digest
def main():
    prefix='/opt/3dgs-runtime/envs/physgaussian';env=runtime_env(prefix);env.update(MAX_JOBS='1',TORCH_CUDA_ARCH_LIST='8.6')
    original=ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting/submodules'
    libs=[];rows=[]
    for name,package in [('simple-knn','simple_knn'),('diff-gaussian-rasterization','diff_gaussian_rasterization')]:
        source=AUDIT/'build'/name/'source';build=source.parent
        assert not source.exists(),'Do not overwrite an earlier build attempt'
        shutil.copytree(original/name,source,ignore=shutil.ignore_patterns('.git','build','__pycache__','*.egg-info'))
        for path in source.rglob('*'):
            if path.is_file():assert digest(path)==digest(original/name/path.relative_to(source))
        library=build/'lib';libs.append(library)
        result=run('cuda-build-'+name,[sys.executable,str(source/'setup.py'),'build_ext','--build-temp',str(build/'temp'),'--build-lib',str(library)],cwd=source,env=env,timeout=1200,required=False);rows.append(result)
        if result['exit_code']!=0:continue
        target=library/package;target.mkdir(exist_ok=True)
        if (source/package).exists():
            for p in (source/package).glob('*.py'):shutil.copy2(p,target/p.name)
        if not (target/'__init__.py').exists():(target/'__init__.py').write_text('')
    save('cuda-build-results.json',rows)
    if any(r['exit_code']!=0 for r in rows):raise SystemExit(1)
    env['PYTHONPATH']=os_pathsep_join(libs)
    code='import torch,simple_knn._C as k,diff_gaussian_rasterization._C as r; print(k.__file__);print(r.__file__);torch.manual_seed(42);x=torch.rand(32,3,device="cuda");actual=k.distCUDA2(x);d=torch.cdist(x,x).square();d.fill_diagonal_(float("inf"));ref=d.topk(3,largest=False).values.mean(1);print("max_knn_abs_error",float((actual-ref).abs().max()));assert torch.allclose(actual,ref,rtol=2e-5,atol=1e-7)'
    rows.append(run('cuda-rebuilt-knn-test',[sys.executable,'-c',code],env=env,required=False))
    # Full render from the same trained PLY using the newly compiled rasterizer.
    old=AUDIT/'outputs/ficus_fresh_30000';new=AUDIT/'outputs/ficus_rebuilt_renderer';new.mkdir()
    shutil.copy2(old/'cfg_args',new/'cfg_args');(new/'point_cloud/iteration_30000').mkdir(parents=True)
    shutil.copy2(old/'point_cloud/iteration_30000/point_cloud.ply',new/'point_cloud/iteration_30000/point_cloud.ply')
    repo=ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting'
    rows.append(run('cuda-rebuilt-render',[sys.executable,str(repo/'render.py'),'-m',str(new),'-s',str(ROOT/'01_PhysGaussian/inputs/nerf_synthetic_ficus'),'--eval','--white_background','--data_device','cpu','--resolution','1','--iteration','30000','--skip_train'],cwd=repo,env=env,required=False))
    if rows[-1]['exit_code']==0:
        import numpy as np
        from PIL import Image
        errors=[]
        for p in sorted((old/'test/ours_30000/renders').glob('*.png')):
            a=np.array(Image.open(p)).astype(float);b=np.array(Image.open(new/'test/ours_30000/renders'/p.name)).astype(float)
            errors.append(float(abs(a-b).max()))
        assert len(errors)==200
        save('checks/rebuilt-render-comparison.json',dict(images=len(errors),maximum_byte_difference=max(errors),exactly_equal_images=sum(v==0 for v in errors),same_PLY_hash=digest(new/'point_cloud/iteration_30000/point_cloud.ply'),rebuilt_libraries=list(map(str,libs))))
    save('cuda-build-results.json',rows)
def os_pathsep_join(paths):
    import os
    return os.pathsep.join(map(str,paths))
if __name__=='__main__':main()
