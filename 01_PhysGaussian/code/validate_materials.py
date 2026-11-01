"""Prescribed-deformation checks of all material switches in upstream kernels.

This is a constitutive audit, not a spatial MPM scene or paper benchmark.
"""
from run_mpm import ROOT,initialize
from warp_windows_compat import enable
from mpm_utils import compute_stress_from_F_trial
import warp as wp
import numpy as np
import json
import matplotlib.pyplot as plt


def make(material,viscosity=100):
    sim=initialize(np.array([[.5,.5,.5]],np.float32),np.array([1e-6],np.float32),
                   np.array([[1e-4,0,0,1e-4,0,1e-4]],np.float32),[0,0,0])
    sim.set_parameters_dict(dict(material=material,E=20000.,nu=.3,density=1000.,yield_stress=200.,
        hardening=0,plastic_viscosity=float(viscosity),softening=600.,friction_angle=30.),device='cuda:0')
    sim.finalize_mu_lam(device='cuda:0')
    return sim


def stress(sim,F,dt=.002):
    sim.mpm_state.particle_F_trial=wp.array(np.asarray(F,np.float32)[None],dtype=wp.mat33,device='cuda:0')
    wp.launch(compute_stress_from_F_trial,dim=1,inputs=[sim.mpm_state,sim.mpm_model,dt],device='cuda:0')
    return sim.mpm_state.particle_stress.numpy()[0],sim.mpm_state.particle_F.numpy()[0]


def main():
    enable();wp.init();out=ROOT/'outputs/material_audit';out.mkdir(parents=True,exist_ok=True)
    mu=20000/(2*1.3);lam=20000*.3/(1.3*.4)
    F=np.diag([1.2,.9,1.05]);J=np.linalg.det(F)
    expected=2*mu*(F-np.eye(3))@F.T+np.eye(3)*lam*J*(J-1)
    actual,_=stress(make('jelly'),F)
    relative=float(np.linalg.norm(actual-expected)/np.linalg.norm(expected));assert relative<1e-5
    angle=.71;R=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
    rotated,_=stress(make('jelly'),R@F)
    objective=float(np.linalg.norm(rotated-R@actual@R.T)/np.linalg.norm(actual));assert objective<1e-5
    rigid,_=stress(make('jelly'),R);assert np.linalg.norm(rigid)<.1
    sand_tension,_=stress(make('sand'),np.eye(3)*1.1);assert np.linalg.norm(sand_tension)<.1
    gamma=np.r_[np.linspace(0,.8,161),np.linspace(.8,0,161)[1:]]
    curves={};metrics={}
    for material in ('jelly','metal','sand','foam','plasticine','snow'):
        sim=make(material);previous=np.eye(3);elastic=np.eye(3);values=[];yields=[];elastic_history=[]
        for value in gamma:
            total=np.eye(3);total[0,1]=value
            trial=total@np.linalg.inv(previous)@elastic
            tau,elastic=stress(sim,trial)
            assert np.isfinite(tau).all() and np.isfinite(elastic).all()
            assert np.linalg.norm(tau-tau.T)<1e-3
            values.append(tau.copy());yields.append(float(sim.mpm_model.yield_stress.numpy()[0]))
            elastic_history.append(elastic.copy());previous=total
        values=np.array(values);curves[material]=values[:,0,1]
        metrics[material]=dict(max_absolute_shear_stress_Pa=float(np.abs(values[:,0,1]).max()),
            residual_shear_stress_Pa=float(values[-1,0,1]),final_yield_stress_Pa=yields[-1],
            final_elastic_F_distance_from_identity=float(np.linalg.norm(elastic-np.eye(3))))
        np.savez_compressed(out/f'{material}.npz',gamma=gamma,stress_Pa=values,elastic_F=elastic_history,yield_stress_Pa=yields)
    assert metrics['metal']['max_absolute_shear_stress_Pa']<metrics['jelly']['max_absolute_shear_stress_Pa']
    assert metrics['plasticine']['final_yield_stress_Pa']<200
    assert metrics['snow']['max_absolute_shear_stress_Pa']==0
    fig,axs=plt.subplots(2,3,figsize=(12,7),layout='constrained')
    for ax,(name,values) in zip(axs.flat,curves.items()):
        ax.plot(gamma[:161],values[:161],label='Load');ax.plot(gamma[160:],values[160:],label='Unload')
        ax.set(title=name+(' (missing stress branch)' if name=='snow' else ''),xlabel='Prescribed shear',ylabel='Kirchhoff shear stress (Pa)');ax.legend()
    fig.savefig(out/'stress_paths.png',dpi=160);plt.close(fig)
    result=dict(scope='official constitutive kernel audit; not paper scene reproduction',all_checks_passed=True,
        elastic_analytic_relative_error=relative,objectivity_relative_error=objective,
        rigid_rotation_stress_norm=float(np.linalg.norm(rigid)),sand_uniform_tension_stress_norm=float(np.linalg.norm(sand_tension)),
        materials=metrics,unsupported='snow maps to material=4, but upstream compute_stress_from_F_trial has no material=4 stress branch; output remains zero')
    text=json.dumps(result,indent=2);(out/'metrics.json').write_text(text);(ROOT/'docs/material-metrics.json').write_text(text)
    print(text,flush=True)


if __name__=='__main__':main()
