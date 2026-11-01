from common import ROOT,AUDIT,save
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
out=AUDIT/'figures';out.mkdir(exist_ok=True)
uniform=json.loads((AUDIT/'checks/V09-convergence.json').read_text());manufactured=json.loads((AUDIT/'checks/V09-manufactured.json').read_text())
print(uniform.keys(),uniform['rows'][0],flush=True)
fig,ax=plt.subplots(figsize=(8,5),layout='constrained')
for label,data in [('Uniform normal derivative / original boundary test',uniform),('Manufactured exact outgoing field / different boundary test',manufactured)]:
 rows=data['rows'];key='relative_complex_error'
 ax.loglog([r['triangles'] for r in rows],[r[key]*100 for r in rows],'o-',label=label)
ax.axhline(.5,ls=':',color='gray',label='0.5% diagnostic target')
ax.set(xlabel='Flat boundary triangle count',ylabel='Relative complex pressure error (%)',title='BEM refinement: preserve both positive and negative evidence');ax.legend(fontsize=8)
fig.savefig(out/'bem_refinement.png',dpi=160);plt.close(fig)
phase=np.load(AUDIT/'pat_phase/outputs/phase_preserving/raw.npz');old=np.load(ROOT/'verification_20261101/pat/outputs/pat_pipeline/pressure_audio_raw.npz');fresh=np.load(ROOT/'verification_20261101/fresh_cpu_pipeline_retry/pat/outputs/pat_pipeline/pressure_audio_raw.npz')
sysroot=ROOT/'02_PAT/code'
import sys
sys.path.insert(0,str(sysroot));from phase_audio import synthesize_phase_preserving
before=[old['pressure_bem_Pa'][0],fresh['pressure_bem_Pa'][0]];after=[synthesize_phase_preserving(old['transfer_bem'],old['modal_response'])[0],synthesize_phase_preserving(fresh['transfer_bem'],fresh['modal_response'])[0]]
fig,axes=plt.subplots(2,1,figsize=(10,6),layout='constrained');time=np.arange(960)/48
for ax,signals,title in zip(axes,[before,after],['Magnitude-only: equivalent FEM bases yield different audio','Phase-preserving extension: equivalent FEM bases agree']):
 for i,s in enumerate(signals):ax.plot(time,s[:960],label=f'Independent FEM solve {i+1}',lw=.8,alpha=.8)
 ax.set(xlabel='Time (ms)',ylabel='Pressure (Pa)',title=title);ax.legend()
fig.savefig(out/'basis_invariance.png',dpi=160);plt.close(fig)
save('checks/CPU-figures.json',dict(files=['figures/bem_refinement.png','figures/basis_invariance.png'],scope='Plots directly from current checks and preserved raw arrays; no perceptual claim.'))
