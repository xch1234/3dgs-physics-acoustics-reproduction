"""Build reviewable scene evidence from completed runs only."""
import json,subprocess,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps,ImageDraw
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]


def main():
    records=[];lines=['# 官方完整场景运行结果','',
        '来源：未修改的 `gs_simulation.py`、官方模型与场景配置。以下只列出保存了最终指标且通过产物检查的运行。',
        '', '通用适配：Taichi 申请从 8 GiB 限为 0.5 GiB；关闭梯度；ASCII 源码软链接绕过 Warp 0.10 的路径编码限制；补充 WSL libcuda 搜索路径。逐帧检查粒子位置、变形梯度有限及总质量保持。',
        '', '六个 official_full 场景使用作者发布的最高迭代 PLY。若列出 ficus_reconstructed_full，则使用本项目重新训练 30,000 步且独立评估的 Ficus，详见 RECONSTRUCTION.md。这里仅汇总动态模拟；外观 PSNR/SSIM/LPIPS 另行计算。显存指标仅统计 PyTorch，不含 Warp/Taichi；计时包含审计，部分场景与 CPU 参考计算并行，Wolf 期间还在确认显存余量后执行过短时网络推理，不能当论文性能。','']
    paths=list((ROOT/'outputs').glob('*official*/metrics.json'))
    own=ROOT/'outputs/ficus_reconstructed_full/metrics.json'
    if own.exists():paths.append(own)
    regularized=ROOT/'outputs/ficus_anisotropy_full/metrics.json'
    if regularized.exists():paths.append(regularized)
    paths.extend((ROOT/'outputs').glob('*_sh_corrected/metrics.json'))
    for path in sorted(paths):
        m=json.loads(path.read_text());out=path.parent
        if not m.get('all_checks_passed'):continue
        frames=sorted(out.glob('*.png'));assert len(frames)==m['rendered_frames']
        with Image.open(frames[0]) as im:size=im.size
        ffprobe=shutil.which('ffprobe') or str(Path(sys.executable).parent/'ffprobe')
        probe=subprocess.run([ffprobe,'-v','error','-count_frames','-select_streams','v:0',
            '-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(out/'output.mp4')],
            capture_output=True,text=True,check=True)
        stream=json.loads(probe.stdout)['streams'][0]
        assert int(stream['nb_read_frames'])==len(frames)
        state=np.load(out/'final_state.npz')
        assert all(np.isfinite(state[k]).all() for k in state.files)
        canvas=Image.new('RGB',(1280,355),'white');draw=ImageDraw.Draw(canvas)
        for j,index in enumerate(np.linspace(0,len(frames)-1,4).astype(int)):
            with Image.open(frames[index]) as im:
                thumb=ImageOps.contain(im.convert('RGB'),(320,320));canvas.paste(thumb,(j*320+(320-thumb.width)//2,25))
            draw.text((j*320+8,6),f'Frame {index+1} / {len(frames)}',fill='black')
        canvas.save(out/'contact_sheet.jpg',quality=92)
        # This JPEG is excluded from the upstream PNG frame count.
        times=[f['time_s'] for f in m['frames']];disp=[f['max_displacement'] for f in m['frames']]
        det=[f['min_det_F'] for f in m['frames']]
        fig,axs=plt.subplots(1,2,figsize=(10,3.6),layout='constrained')
        axs[0].plot(times,disp);axs[0].set(xlabel='Simulation time (s)',ylabel='Maximum particle displacement (MPM units)')
        axs[1].plot(times,det);axs[1].set(xlabel='Simulation time (s)',ylabel='Minimum det(F_trial)')
        fig.savefig(out/'state_audit.pdf');plt.close(fig)
        row=dict(scene=out.name,particles=m['physical_particles'],steps=m['steps'],simulation_seconds=m['duration_s'],
            frames=len(frames),image_size=size,video=stream,max_displacement=max(disp),minimum_det_F=min(det),
            elapsed_s=m['elapsed_s'],checkpoint=m['model_checkpoint'],model_sha256=m['model_sha256'])
        records.append(row)
        lines += [f'## {out.name}','',f'- {row["particles"]:,} 粒子，{row["steps"]:,} 子步，{row["simulation_seconds"]:g} 秒；{row["frames"]} 帧，{size[0]}×{size[1]}。',
            f'- 最大位移 {max(disp):.7g}（MPM 坐标单位），全程最小 det(F_trial)={min(det):.7g}；总用时 {m["elapsed_s"]:.1f} 秒。',
            f'- 检查点：`{Path(m["model_checkpoint"]).parent.name}`，SHA256 `{m["model_sha256"]}`。',
            f'- [视频](../outputs/{out.name}/output.mp4) · [四帧预览](../outputs/{out.name}/contact_sheet.jpg) · [状态曲线](../outputs/{out.name}/state_audit.pdf) · [完整指标](../outputs/{out.name}/metrics.json)','']
    lines += ['## 判读边界','',
        '三个 *_sh_corrected 场景另加了 SH 旋转坐标基转换。每帧保存同一物理状态的原版/修复版图像差异；不是未修改渲染行为，详见 SH_CORRECTED_SCENES.md。','',
        'ficus_anisotropy_full 若出现，使用单独训练的式(12)正则化模型，阈值5、权重0.01为本地预定值。它不是作者发布模型或原图8场景；见 ANISOTROPY_RESULTS.md。','',
        'Wolf 保留上游 `step_per_frame = int(frame_dt / substep_dt)`：Python 浮点下 0.04 / 2e-5 略小于 2000，截断为每帧 1999 步。因此原 50 帧实际为 99,950 子步、1.999 秒，视频仍为 25 fps / 2 秒。这是原代码行为，不是本次人为减少步数；未修改上游计算以凑名义数值。', '',
        '有限值和质量守恒是基础数值检查，不等于物理模型已由实验测量验证。塑性或颗粒场景中的 F_trial 也不能直接当作最终弹性变形梯度。原始配置失败及适配运行应分别查阅日志与继续执行记录。']
    (ROOT/'docs/OFFICIAL_SCENES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (ROOT/'docs/official-scenes-verified.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print(json.dumps(records,indent=2))


if __name__=='__main__':main()
