"""Compare fresh and saved equivalent FEM bases, and resulting raw audio."""
import json
import numpy as np
from common import ROOT,AUDIT,save
old=np.load(ROOT/'02_PAT/inputs/official_fem_result.npz')
new=np.load(AUDIT/'fresh_cpu_pipeline_retry/fem/official_fem_result.npz')
matrix_errors={k:float(np.linalg.norm(new[k]-old[k])/np.linalg.norm(old[k])) for k in ('K_N_per_m','M_kg')}
for value in matrix_errors.values():assert value<1e-12
freq_error=float(np.max(abs(new['frequencies_Hz']/old['frequencies_Hz']-1)));assert freq_error<1e-10
free=old['free_dofs'];mass=old['M_kg'][np.ix_(free,free)];u=old['clamped_modes_mass_normalized'][:,:6];v=new['clamped_modes_mass_normalized'][:,:6]
singular=np.linalg.svd(u.T@mass@v,compute_uv=False);assert np.max(abs(singular-1))<1e-10
a=np.load(AUDIT/'pat/outputs/pat_pipeline/pressure_audio_raw.npz')
b=np.load(AUDIT/'fresh_cpu_pipeline_retry/pat/outputs/pat_pipeline/pressure_audio_raw.npz')
x=u@a['modal_response'][:,::100];y=v@b['modal_response'][:,::100]
vibration_error=float(np.linalg.norm(y-x)/np.linalg.norm(x));assert vibration_error<1e-8
audio_error=float(np.linalg.norm(b['pressure_bem_Pa']-a['pressure_bem_Pa'])/np.linalg.norm(a['pressure_bem_Pa']))
rms_ratio=(np.linalg.norm(b['pressure_bem_Pa'],axis=1)/np.linalg.norm(a['pressure_bem_Pa'],axis=1)).tolist()
complex_a=a['transfer_bem']@a['modal_response'][:,::100]
complex_b=b['transfer_bem']@b['modal_response'][:,::100]
complex_error=float(np.linalg.norm(complex_b-complex_a)/np.linalg.norm(complex_a));assert complex_error<1e-8
result=dict(matrix_relative_errors=matrix_errors,max_frequency_relative_error=freq_error,first_six_mass_inner_product_singular_values=singular.tolist(),reconstructed_displacement_relative_L2=vibration_error,BEM_magnitude_audio_relative_L2=audio_error,listener_RMS_ratios=rms_ratio,modal_basis_invariant_displacement_passed=True,modal_basis_invariant_audio_passed=audio_error<1e-6,explanation='Same FEM matrices/frequencies and invariant physical displacement, but magnitude-only abs(transfer) @ modal_response discards mode-dependent pressure phase/sign. Equivalent eigensolver bases can yield different raw sound. This check does not claim perceptual difference or change the original implementation.')
result['complex_transfer_control_relative_L2']=complex_error
save('checks/fem-basis-audio-invariance.json',result)
print(json.dumps(result,indent=2))
