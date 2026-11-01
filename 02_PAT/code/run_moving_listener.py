"""PAT runtime: moving receiver, repeated physical modal impulses and scaling.

Uses already fitted 12-mode multipoles and the saved BEM densities; no refit.
Pressure magnitude modulation follows the paper approximation (no Doppler).
"""
import run_pat_extended as ext
import json,time
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
base=ext.base;ROOT=base.ROOT;OUT=ROOT/'outputs/moving_listener'


def main():
    OUT.mkdir(parents=True,exist_ok=True);data=dict(np.load(base.FEM))
    saved=dict(np.load(ext.OUT/'beam_mesh.npz'));mesh=ext.geometry(saved['vertices'],saved['triangles'])
    modes=[dict(np.load(ext.OUT/f'mode_{j+1:02d}.npz')) for j in range(12)]
    freq=data['frequencies_Hz'];k=2*np.pi*freq/343
    def evaluate(points,method):
        return np.column_stack([ext.evaluate(points,m['centers'],m['coefficients'],k[j]) if method=='pat'
            else ext.pressure(points,mesh,k[j],m['density']) for j,m in enumerate(modes)])
    controls=np.linspace(0,3,601);angle=2*np.pi*controls/3
    positions=np.c_[.25*np.cos(angle),.25*np.sin(angle),.08*np.sin(2*angle)]
    b=evaluate(positions,'bem');p=evaluate(positions,'pat')
    map_error=float(np.linalg.norm(p-b)/np.linalg.norm(b))
    fs=48000;t=np.arange(fs*3)/fs;vertices=data['vertices_m']
    hit=int(np.argmax(vertices@np.array([1,.1,.01])))
    full=np.zeros((len(vertices)*3,12));full[data['free_dofs']]=data['clamped_modes_mass_normalized']
    impulse=full.reshape(-1,3,12)[hit,1]*.001
    omega=2*np.pi*freq;decay=(30+1e-6*omega**2)/2;wd=np.sqrt(omega**2-decay**2)
    q=np.zeros((12,len(t)))
    for event in np.arange(0,3,.5):
        age=np.maximum(t-event,0)
        q+=impulse[:,None]/wd[:,None]*np.exp(-decay[:,None]*age)*np.sin(wd[:,None]*age)*(t>=event)
    signals={}
    for name,transfer in [('bem',b),('pat',p)]:
        gain_field=np.array([np.interp(t,controls,np.abs(transfer[:,j])) for j in range(12)])
        signals[name]=(gain_field*q).sum(axis=0)
    gain=.85/max(np.abs(a).max() for a in signals.values());fade=np.ones(len(t));fade[-960:]=np.linspace(1,0,960)
    for name,sig in signals.items():wavfile.write(OUT/f'{name}_moving.wav',fs,np.rint(sig*gain*fade*32767).astype(np.int16))
    np.savez_compressed(OUT/'raw.npz',time_s=t,bem_pressure_Pa=signals['bem'],pat_pressure_Pa=signals['pat'],
        common_gain=gain,control_time_s=controls,receiver_positions_m=positions,bem_transfer=b,pat_transfer=p)
    timings=[]
    for count in (1,8,64,256):
        points=base.sphere_points(count,.25,.391)
        evaluate(points,'pat');evaluate(points,'bem')
        result=dict(receivers=count)
        for method in ('pat','bem'):
            times=[]
            for _ in range(3):
                start=time.perf_counter();evaluate(points,method);times.append(time.perf_counter()-start)
            result[method+'_seconds']=times
            result[method+'_median_seconds']=float(np.median(times))
        result['observed_speed_ratio']=result['bem_median_seconds']/result['pat_median_seconds']
        timings.append(result);print(result,flush=True)
    audio_error=float(np.linalg.norm(signals['pat']-signals['bem'])/np.linalg.norm(signals['bem']))
    metrics=dict(scope='PAT moving receiver and output-count evaluation on saved small beam',all_checks_passed=map_error<.05 and audio_error<.05,
        control_samples=len(controls),control_rate_hz=200,frequency_modes=12,duration_s=3,impulse_times_s=list(np.arange(0,3,.5)),
        complex_transfer_relative_L2=map_error,audio_relative_L2=audio_error,timings=timings,
        limitations=['amplitude-only paper acoustic transfer approximation','no Doppler or propagation delay','same scripted impulse every 0.5s, no collision engine',
        'local Python timings with other background experiments, not original 7000x benchmark','both methods reuse precomputation; BEM timings are saved-density potential evaluation'])
    assert metrics['all_checks_passed'],metrics
    payload=json.dumps(metrics,indent=2);(OUT/'metrics.json').write_text(payload);(ROOT/'docs/moving-listener-metrics.json').write_text(payload)
    fig,axs=plt.subplots(1,3,figsize=(14,4),layout='constrained')
    axs[0].plot(positions[:,0],positions[:,1]);axs[0].set_aspect('equal');axs[0].set(xlabel='Receiver x (m)',ylabel='Receiver y (m)',title='Moving receiver path')
    axs[1].plot(t,signals['bem'],label='BEM',lw=.6);axs[1].plot(t,signals['pat'],label='PAT',lw=.5,alpha=.7);axs[1].legend();axs[1].set(xlabel='Time (s)',ylabel='Pressure (Pa)',title='Repeated identical impacts')
    for method in ('pat','bem'):axs[2].loglog([r['receivers'] for r in timings],[r[method+'_median_seconds'] for r in timings],'o-',label=method)
    axs[2].legend();axs[2].set(xlabel='Receiver count',ylabel='12-mode evaluation (s)',title='Observed runtime / local Python')
    fig.savefig(OUT/'moving_receiver.png',dpi=160);plt.close(fig)
    report=f'''# PAT 移动听者与运行时求值

使用已保存的 12 模态、1792 面片 BEM 密度及多极子系数，不重新拟合。听者在半径 0.25 m 的环形路径运动，高度同时变化；每 0.5 秒施加相同的 0.001 N·s 模态冲量，持续 3 秒。传递函数以 200 Hz 更新并插值至 48 kHz 音频。

复声压传递相对误差 {map_error:.3%}，合成声压音频相对误差 {audio_error:.3%}。BEM 与 PAT 使用同一个播放增益，保留未经归一化的 Pa 波形。遵循论文的幅值传递近似，未包含多普勒、传播延迟或接触碰撞求解。

- [PAT 移动听者音频](../outputs/moving_listener/pat_moving.wav)
- [BEM 对照音频](../outputs/moving_listener/bem_moving.wav)
- [路径、波形和运行时间图](../outputs/moving_listener/moving_receiver.png)
- [完整参数与计时](moving-listener-metrics.json)

对 1、8、64、256 个听者分别预热后计时三次，保存所有时间与中位数。两种方法均复用预计算，BEM 测量的是边界密度到外场的求值。此为本地 Python 实现且可能受后台任务影响，不能宣称复现论文的 7000 倍性能。

重跑：在项目 acoustics Conda 中运行 `python 02_PAT/code/run_moving_listener.py`，先确保扩展实验已生成全部 mode NPZ。
'''
    (ROOT/'docs/MOVING_LISTENER.md').write_text(report,encoding='utf-8')
    print(payload,flush=True)


if __name__=='__main__':main()
