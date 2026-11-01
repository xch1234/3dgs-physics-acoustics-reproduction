"""Opt-in local snow constitutive extension; NOT released PhysGaussian behavior.

Fixed-corotated elasticity with SVD stretch clamping (compression .025,
stretch .0075), multiplicative plastic volume and exp(10*(1-Jp)) hardening.
Default limits follow the common snow-MPM model; Jp is clipped to [.6,20]
for numerical safety. Not calibrated to a specific snow sample.
"""
import warp as wp
import numpy as np
from warp_utils import MPMStateStruct,MPMModelStruct
from mpm_utils import kirchoff_stress_FCR

@wp.kernel
def snow_stress(state: MPMStateStruct, model: MPMModelStruct, dt: float):
    p=wp.tid()
    if state.particle_selection[p]==0:
        F=state.particle_F_trial[p]
        U=wp.mat33(0.0);V=wp.mat33(0.0);s=wp.vec3(0.0)
        wp.svd3(F,U,s,V)
        clipped=wp.vec3(wp.clamp(s[0],0.975,1.0075),wp.clamp(s[1],0.975,1.0075),wp.clamp(s[2],0.975,1.0075))
        Fe=U*wp.diag(clipped)*wp.transpose(V)
        jp=wp.clamp(state.particle_Jp[p]*wp.determinant(F)/wp.determinant(Fe),0.6,20.0)
        state.particle_Jp[p]=jp
        hardening=wp.exp(10.0*(1.0-jp))
        tau=kirchoff_stress_FCR(Fe,U,V,wp.determinant(Fe),model.mu[p]*hardening,model.lam[p]*hardening)
        state.particle_F[p]=Fe
        state.particle_stress[p]=(tau+wp.transpose(tau))/2.0

def initialize_plastic_volume(simulator, device='cuda:0'):
    """Initialize new snow only; never call this when resuming plastic history."""
    count=simulator.mpm_state.particle_x.shape[0]
    simulator.mpm_state.particle_Jp=wp.array(np.ones(count,np.float32),dtype=float,device=device)


def install(solver_module):
    """Dispatch only material=4 to the local kernel, preserving other materials.

    Returns a context manager; no on-disk upstream code is modified.
    All snow particles must start with plastic determinant Jp=1.
    """
    from contextlib import contextmanager
    @contextmanager
    def context():
        original=solver_module.wp.launch
        checked={}
        def dispatch(kernel,*args,**kwargs):
            inputs=kwargs.get('inputs',args[1] if len(args)>1 else [])
            if kernel is solver_module.compute_stress_from_F_trial and len(inputs)>1 and inputs[1].material==4:
                key=inputs[0].particle_Jp.ptr
                if key not in checked:
                    initial=inputs[0].particle_Jp.numpy()
                    if not np.isfinite(initial).all() or (initial<=0).any():
                        raise ValueError('Snow plastic determinant must be positive. Initialize new snow with initialize_plastic_volume(simulator); preserve Jp when resuming.')
                    checked[key]=inputs[0].particle_Jp
                return original(snow_stress,*args,**kwargs)
            return original(kernel,*args,**kwargs)
        solver_module.wp.launch=dispatch
        try:yield
        finally:solver_module.wp.launch=original
    return context()
