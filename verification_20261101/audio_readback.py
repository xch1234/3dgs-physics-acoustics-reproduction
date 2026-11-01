"""Independently derive PCM and transfer-to-pressure from saved raw arrays."""
import sys,json,wave
import numpy as np
from common import ROOT,AUDIT,save,digest

def read(p):
    with wave.open(str(p)) as f:
        assert f.getsampwidth()==2 and f.getnchannels()==1
        return f.getframerate(),np.frombuffer(f.readframes(f.getnframes()),'<i2')

def main():
    rows=[]
    jobs=[
      (ROOT/'02_PAT/outputs/pat_pipeline','pressure_audio_raw.npz',{'pressure_bem_Pa':'bem_listener_{}','pressure_pat_Pa':'pat_listener_{}'},'xyz'),
      (AUDIT/'pat/outputs/pat_pipeline','pressure_audio_raw.npz',{'pressure_bem_Pa':'bem_listener_{}','pressure_pat_Pa':'pat_listener_{}'},'xyz'),
      (ROOT/'02_PAT/outputs/pat_extended','audio_raw.npz',{'bem_pressure_Pa':'bem_{}','pat_pressure_Pa':'pat_{}'},'xyz'),
      (ROOT/'02_PAT/outputs/moving_listener','raw.npz',{'bem_pressure_Pa':'bem_moving','pat_pressure_Pa':'pat_moving'},['']),
      (ROOT/'03_NeuralSound/outputs/neural_audio','raw.npz',{'bem_pressure_Pa':'bem_listener_{}','neural_pressure_Pa':'neural_listener_{}'},[1,2,3])]
    for folder,raw,keys,labels in jobs:
        a=np.load(folder/raw);t=a['time_s'];fs=round(1/(t[1]-t[0]));gain=float(a['common_gain']);assert gain>0
        fade=np.ones(len(t));fade[-960:]=np.linspace(1,0,960)
        signals=[]
        for key,pattern in keys.items():
            data=np.atleast_2d(a[key]);assert data.shape==(len(labels),len(t));assert np.isfinite(data).all();signals.append(data)
            for signal,label in zip(data,labels):
                path=folder/(pattern.format(label)+'.wav');sr,pcm=read(path)
                assert sr==fs and np.max(np.abs(signal*gain))<1
                expected=np.rint(signal*gain*fade*32767).astype('<i2');np.testing.assert_array_equal(pcm,expected)
                rows.append(dict(file=str(path.relative_to(ROOT)),sample_rate=sr,samples=len(pcm),peak=int(abs(pcm.astype(int)).max()),exact_PCM=True,sha256=digest(path)))
        if 'modal_response' in a and 'transfer_bem' in a:
            np.testing.assert_allclose(a['pressure_bem_Pa'],abs(a['transfer_bem'])@a['modal_response'],rtol=1e-12,atol=1e-14)
            np.testing.assert_allclose(a['pressure_pat_Pa'],abs(a['transfer_pat'])@a['modal_response'],rtol=1e-12,atol=1e-14)
        rows.append(dict(raw=str((folder/raw).relative_to(ROOT)),relative_audio_L2=float(np.linalg.norm(signals[1]-signals[0])/np.linalg.norm(signals[0])),common_gain=gain))
    folder=ROOT/'reproduction/traditional/outputs'
    cases=['baseline','stiffness_x4','mass_x4','damping_x4','hit_middle'];parts=[]
    for name in cases:
        sr,pcm=read(folder/(name+'.wav'));parts.extend([pcm,np.zeros(sr//2,dtype=np.int16)])
    sr,pcm=read(folder/'comparison_all.wav');np.testing.assert_array_equal(pcm,np.concatenate(parts))
    rows.append(dict(file=str((folder/'comparison_all.wav').relative_to(ROOT)),exact_PCM=True,samples=len(pcm)))
    save('checks/audio-readback.json',dict(passed=True,records=rows,limitation='Numeric waveform/PCM validation; no human listening test, and no fresh neural or moving-listener audio synthesis.'))
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
