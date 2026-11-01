"""Independently audit saved A1 arrays/audio without regenerating old outputs."""
import json
import wave
from datetime import datetime
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp

ROOT=Path(__file__).resolve().parents[1]


def main():
    folder=ROOT/'reproduction/traditional/outputs'
    metrics=json.loads((folder/'metrics.json').read_text(encoding='utf-8'))
    p=metrics['parameters'];n=p['masses'];fs=p['sample_rate_Hz']
    gain=metrics['playback_common_gain_per_m_per_s'];records=[];arrays={};playback=[]
    for name,case in metrics['cases'].items():
        with np.load(folder/f'{name}_raw.npz') as data:
            a={key:data[key] for key in data.files}
        assert all(np.isfinite(v).all() for v in a.values())
        M,K,U,E=a['M_kg'],a['K_N_per_m'],a['modes_mass_normalized'],a['eigenvalues']
        # Assemble spring contributions independently from each pair of endpoints.
        reference_K=np.zeros((n,n));stiffness=p['spring_stiffness_N_per_m']*case['stiffness_scale']
        reference_K[0,0]=stiffness
        for i in range(1,n):
            reference_K[i,i]+=stiffness;reference_K[i-1,i-1]+=stiffness
            reference_K[i,i-1]-=stiffness;reference_K[i-1,i]-=stiffness
        np.testing.assert_allclose(K,reference_K)
        np.testing.assert_allclose(M,np.eye(n)*p['mass_kg']*case['mass_scale'])
        assert E.min()>0
        residual=np.linalg.norm(K@U-(M@U)*E,axis=0)/(np.linalg.norm(K@U,axis=0)+np.linalg.norm((M@U)*E,axis=0))
        assert residual.max()<1e-10
        np.testing.assert_allclose(U.T@M@U,np.eye(n),atol=1e-12)
        np.testing.assert_allclose(a['frequencies_Hz'],np.sqrt(E)/(2*np.pi))
        keep=(a['frequencies_Hz']>=p['minimum_frequency_Hz'])&(a['frequencies_Hz']<min(p['maximum_frequency_Hz'],.45*fs))
        np.testing.assert_array_equal(a['retained'],keep)
        impulse=np.zeros(n);impulse[case['hit_node_1based']-1]=p['impulse_N_s']
        np.testing.assert_allclose(a['modal_initial_velocity'],U.T@impulse,atol=1e-14)
        expected_decay=case['damping_scale']*(p['rayleigh_alpha_per_s']+p['rayleigh_beta_s']*E)/2
        np.testing.assert_allclose(a['decay_rate_per_s'],expected_decay)
        np.testing.assert_allclose(a['time_s'],np.arange(round(fs*p['duration_s']))/fs)
        assert np.diff(a['energy_J']).max()<=a['energy_J'][0]*1e-10
        expected_energy=.5*np.sum(a['modal_initial_velocity'][keep]**2)
        np.testing.assert_allclose(a['energy_J'][0],expected_energy)
        fade=np.ones_like(a['time_s']);fade[-round(p['playback_tail_fade_s']*fs):]=np.linspace(1,0,round(p['playback_tail_fade_s']*fs))
        expected_pcm=np.rint(a['velocity_m_per_s']*gain*fade*32767).astype('<i2')
        with wave.open(str(folder/f'{name}.wav')) as f:
            assert (f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes())==(1,2,fs,len(expected_pcm))
            pcm=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2')
        np.testing.assert_array_equal(pcm,expected_pcm)
        assert 0<np.abs(pcm.astype(np.int32)).max()<32767
        playback.extend([pcm,np.zeros(fs//2,dtype='<i2')]);arrays[name]=a
        records.append(dict(case=name,max_eigenpair_residual=float(residual.max()),retained_modes=int(keep.sum()),shared_gain_PCM_exact=True))
    b=arrays['baseline']
    np.testing.assert_allclose(arrays['stiffness_x4']['frequencies_Hz'],2*b['frequencies_Hz'])
    np.testing.assert_allclose(arrays['mass_x4']['frequencies_Hz'],.5*b['frequencies_Hz'])
    np.testing.assert_allclose(arrays['hit_middle']['frequencies_Hz'],b['frequencies_Hz'])
    assert not np.allclose(np.abs(arrays['hit_middle']['modal_initial_velocity']),np.abs(b['modal_initial_velocity']))
    assert arrays['damping_x4']['energy_J'][1000]<b['energy_J'][1000]
    with wave.open(str(folder/'comparison_all.wav')) as f:
        combined=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2')
    np.testing.assert_array_equal(combined,np.concatenate(playback))
    # Reintegrate the physical coordinates, sampling actual saved waveform times.
    times=b['time_s'][:481];C=p['rayleigh_alpha_per_s']*b['M_kg']+p['rayleigh_beta_s']*b['K_N_per_m']
    v0=np.zeros(n);v0[-1]=p['impulse_N_s']/p['mass_kg']
    ode=solve_ivp(lambda t,y:np.r_[y[n:],-(b['K_N_per_m']@y[:n]+C@y[n:])/np.diag(b['M_kg'])],
        (0,times[-1]),np.r_[np.zeros(n),v0],t_eval=times,method='DOP853',rtol=1e-10,atol=1e-13)
    assert ode.success
    error=float(np.max(np.abs(ode.y[-1]-b['velocity_m_per_s'][:len(times)]))/np.max(np.abs(ode.y[-1])))
    assert error<1e-7
    result=dict(passed=True,time=datetime.now().astimezone().isoformat(),records=records,
        physical_ODE_vs_saved_velocity_relative_max_error=error,combined_audio_exact=True,
        note='Read-only verification of original A1 outputs; vibration sonification, not radiated pressure.')
    (ROOT/'reproduction/audit/traditional-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (ROOT/'reproduction/traditional/ACCEPTANCE.md').write_text('# 原计划 A1 独立验收\n\n'
        '重新读回五组原始 NPZ、五段 WAV 和总对照 WAV，原文件未重写。独立按弹簧端点装配 K，核对质量矩阵、正特征值、质量正交、冲量投影、Rayleigh 阻尼、奈奎斯特截断、能量衰减和共同播放增益。五段 PCM 与原始速度乘同一增益后量化的结果逐样本完全一致，总音频亦逐样本一致。\n\n'
        f'独立物理坐标 DOP853 积分与已保存速度的相对最大误差 {error:.6g}。刚度×4频率×2、质量×4频率×0.5、阻尼增大衰减加快、敲击点改变激发而不改变频率均通过。\n\n'
        '[机器记录](../audit/traditional-audit.json) · [原始结果](outputs/RESULTS.zh-CN.md)。本实验是振动可听化，不是声压或 PAT 复现。\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
