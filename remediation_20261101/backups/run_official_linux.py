"""Run upstream gs_simulation.py with a memory cap and independent state audit.

No model, material, camera or rendering replacements. Only lower Taichi's
requested allocation from 8 GiB to 0.5 GiB for this 4 GiB GPU, and disable grads.
"""
import os
os.environ['OMP_NUM_THREADS']='1'
import sys
import runpy
import json
import time
import argparse
import hashlib
import importlib
from pathlib import Path
import numpy as np
import torch
import taichi as ti

ROOT=Path(__file__).resolve().parents[1]
REPO=Path(os.environ.get('PHYSGAUSSIAN_SOURCE',str(ROOT/'code/PhysGaussian')))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default=str(REPO/'config/ficus_config.json'))
    parser.add_argument('--model',default=str(ROOT/'inputs/ficus_whitebg-trained'))
    parser.add_argument('--tag',default='ficus_official_full')
    parser.add_argument('--correct-sh-frame',action='store_true',help='Opt-in external basis conversion for SH inverse rotations; preserve original runs separately')
    args=parser.parse_args()
    args.model=str(Path(args.model).resolve());args.config=str(Path(args.config).resolve())
    out=ROOT/'outputs'/args.tag;out.mkdir(parents=True,exist_ok=True)
    config=json.loads(Path(args.config).read_text())
    checkpoints=sorted((Path(args.model)/'point_cloud').glob('iteration_*'),key=lambda p:int(p.name.split('_')[-1]))
    source_ply=checkpoints[-1]/'point_cloud.ply'
    source_hash=hashlib.sha256(source_ply.read_bytes()).hexdigest()
    (out/'config.json').write_text(json.dumps(config,indent=2))
    original_init=ti.init
    def memory_limited_init(*a,**kw):
        kw['device_memory_GB']=.5
        return original_init(*a,**kw)
    ti.init=memory_limited_init
    torch.set_grad_enabled(False)
    torch.cuda.reset_peak_memory_stats()
    os.chdir(REPO)
    # The upstream solver appends realpath(__file__), which reintroduces the
    # Unicode workspace through its top-level mpm_utils/engine_utils imports.
    # Prefer the existing read-only ASCII alias for those leaf modules too.
    sys.path.insert(0,str(REPO))
    # Establish the namespace package before adding its leaf directory, which
    # also contains a same-named .py file and would otherwise shadow it.
    importlib.import_module('mpm_solver_warp')
    sys.path.insert(1,str(REPO/'mpm_solver_warp'))
    sys.path.append(str(REPO/'gaussian-splatting'))
    sh_comparisons=[]
    if args.correct_sh_frame:
        from utils import render_utils,transformation_utils
        from sh_frame_adapter import inverse_rotation_to_world
        from torchvision.utils import save_image
        matrices=transformation_utils.generate_rotation_matrices(
            torch.tensor(config.get('rotation_degree',[0.])),config.get('rotation_axis',[0]))
        original_convert=render_utils.convert_SH
        original_initialize=render_utils.initialize_resterize
        comparison_state={}
        comparison_folder=out/'same_state_comparison';comparison_folder.mkdir(exist_ok=True)
        selected_frames=set(np.linspace(1,config['frame_num'],4).astype(int))
        def converted_sh(shs,camera,gaussians,position,rotation=None):
            comparison_state['uncorrected_colors']=original_convert(shs,camera,gaussians,position,rotation)
            return original_convert(shs,camera,gaussians,position,inverse_rotation_to_world(rotation,matrices))
        def paired_initialize(*a,**kw):
            rasterizer=original_initialize(*a,**kw)
            def paired_rasterizer(**render_args):
                corrected=rasterizer(**render_args)
                original_args=dict(render_args,colors_precomp=comparison_state.pop('uncorrected_colors'))
                uncorrected=rasterizer(**original_args)
                delta=corrected[0]-uncorrected[0]
                frame=len(sh_comparisons)+1
                sh_comparisons.append(dict(frame=frame,relative_image_L2=float(torch.linalg.norm(delta)/torch.linalg.norm(uncorrected[0]).clamp_min(1e-12)),
                    mean_absolute_difference=float(delta.abs().mean()),max_absolute_difference=float(delta.abs().max())))
                if frame in selected_frames:
                    save_image(uncorrected[0],comparison_folder/f'frame_{frame:04d}_original.png')
                    save_image(corrected[0],comparison_folder/f'frame_{frame:04d}_corrected.png')
                    np.savez_compressed(comparison_folder/f'frame_{frame:04d}_raw.npz',frame=np.int32(frame),
                        original=uncorrected[0].cpu().numpy(),corrected=corrected[0].cpu().numpy())
                return corrected
            return paired_rasterizer
        render_utils.convert_SH=converted_sh
        render_utils.initialize_resterize=paired_initialize
    from mpm_solver_warp.mpm_solver_warp import MPM_Simulator_WARP
    kernel_modules={name:str(sys.modules[name].__file__) for name in ('mpm_utils','engine_utils','warp_utils')}
    print('WARP_SOURCE_MODULES',kernel_modules,flush=True)
    original_step=MPM_Simulator_WARP.p2g2p
    checks=[];initial={};calls=0;last_solver=None
    stride=int(config['frame_dt']/config['substep_dt'])
    def audited_step(self,*a,**kw):
        nonlocal calls,last_solver
        last_solver=self
        if calls==0:
            initial['positions']=self.mpm_state.particle_x.numpy().copy()
            initial['mass']=float(self.mpm_state.particle_mass.numpy().sum())
        result=original_step(self,*a,**kw);calls+=1
        if calls%stride==0:
            x=self.mpm_state.particle_x.numpy()
            F=self.mpm_state.particle_F_trial.numpy()
            assert np.isfinite(x).all() and np.isfinite(F).all()
            mass=float(self.mpm_state.particle_mass.numpy().sum())
            assert np.isclose(mass,initial['mass'],rtol=1e-6)
            checks.append(dict(frame=calls//stride,time_s=calls*config['substep_dt'],
                max_displacement=float(np.linalg.norm(x-initial['positions'],axis=1).max()),
                min_det_F=float(np.linalg.det(F).min()),mass=mass))
            (out/'frame-audit.json').write_text(json.dumps(checks,indent=2))
        return result
    MPM_Simulator_WARP.p2g2p=audited_step
    sys.argv=['gs_simulation.py','--model_path',str(Path(args.model).resolve()),'--output_path',str(out),
              '--config',str(Path(args.config).resolve()),'--render_img','--compile_video','--white_bg']
    start=time.perf_counter()
    runpy.run_path(str(REPO/'gs_simulation.py'),run_name='__main__')
    torch.cuda.synchronize()
    np.savez_compressed(out/'final_state.npz',initial_positions=initial['positions'],
        final_positions=last_solver.mpm_state.particle_x.numpy(),final_F=last_solver.mpm_state.particle_F_trial.numpy(),
        final_covariance=last_solver.mpm_state.particle_cov.numpy())
    assert len(checks)==config['frame_num']
    assert len(list(out.glob('*.png')))==config['frame_num']
    assert (out/'output.mp4').stat().st_size>10000
    metrics=dict(scope='upstream full gs_simulation MPM and perspective SH CUDA rendering',all_checks_passed=True,
        physical_particles=len(initial['positions']),steps=calls,duration_s=calls*config['substep_dt'],
        model_checkpoint=str(source_ply),model_sha256=source_hash,
        rendered_frames=len(checks),sh_frame_correction=args.correct_sh_frame,torch_version=torch.__version__,torch_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        warp_source_modules=kernel_modules,
        torch_peak_reserved_bytes=torch.cuda.max_memory_reserved(),elapsed_s=time.perf_counter()-start,
        adaptations=['Taichi device_memory_GB capped at 0.5 instead of upstream 8','torch no_grad','external per-frame state audits','ASCII symlink for Warp generated CUDA source path comments','WSL libcuda dynamic library path'],
        memory_note='PyTorch peak excludes Warp and Taichi allocations',frames=checks)
    payload=json.dumps(metrics,indent=2)
    if args.correct_sh_frame:
        assert len(sh_comparisons)==config['frame_num']
        metrics['adaptations'].append('Opt-in conjugation of MPM inverse rotation into the world basis for SH; same-state paired original/corrected rendering')
        metrics['sh_same_state_comparison']=sh_comparisons
        payload=json.dumps(metrics,indent=2)
    (out/'metrics.json').write_text(payload)
    (ROOT/'docs'/f'{args.tag}-metrics.json').write_text(payload)
    print(payload,flush=True)


if __name__=='__main__':main()
