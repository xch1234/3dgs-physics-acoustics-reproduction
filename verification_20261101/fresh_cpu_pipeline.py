"""Actually recompute FEM, then feed those new modes into the local PAT pipeline."""
import os,sys,json
from common import ROOT,AUDIT,save,digest
os.environ['NUMBA_CACHE_DIR']=str(AUDIT/'cache/numba_fem')
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='core.autocrlf',GIT_CONFIG_VALUE_0='true')
sys.path.insert(0,str(ROOT/'03_NeuralSound/code'))
import run_official_fem as fem
fem.OUT=AUDIT/'fresh_cpu_pipeline_retry/fem'
fem.main()
sys.path.insert(0,str(ROOT/'02_PAT/code'))
import run_pat as pat
pat.ROOT=AUDIT/'fresh_cpu_pipeline_retry/pat'
(pat.ROOT/'docs').mkdir(parents=True,exist_ok=True)
pat.OUT=pat.ROOT/'outputs/pat_pipeline'
pat.FEM=fem.OUT/'official_fem_result.npz'
pat.main()
import numpy as np
from scipy.io import wavfile
a=np.load(pat.OUT/'pressure_audio_raw.npz');fade=np.ones(len(a['time_s']));fade[-960:]=np.linspace(1,0,960)
for key,name in [('pressure_bem_Pa','bem'),('pressure_pat_Pa','pat')]:
    for i,axis in enumerate('xyz'):
        sr,pcm=wavfile.read(pat.OUT/(name+'_listener_'+axis+'.wav'))
        expected=np.rint(a[key][i]*float(a['common_gain'])*fade*32767).astype(np.int16)
        assert sr==48000;np.testing.assert_array_equal(pcm,expected)
save('checks/fresh-fem-pat-chain.json',dict(passed=True,FEM_source=str(pat.FEM.relative_to(AUDIT)),FEM_SHA256=digest(pat.FEM),audio_relative_L2=float(np.linalg.norm(a['pressure_pat_Pa']-a['pressure_bem_Pa'])/np.linalg.norm(a['pressure_bem_Pa'])),WAV_exact_PCM=6,scope='Fresh 24-voxel beam FEM/Lanczos -> six-mode local BEM/PAT fit -> six WAV files; not original PAT benchmark or unified 3DGS geometry.'))
