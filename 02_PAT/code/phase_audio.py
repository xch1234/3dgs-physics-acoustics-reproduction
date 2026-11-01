"""Linear phase-preserving modal audio; narrow-band frequency-domain approximation.

A complex transfer coefficient is evaluated at each modal frequency. Applying it
on the analytic (Hilbert) modal signal preserves phase and covariance under real
basis changes. This is not a causal broadband transient boundary solver.
"""
import numpy as np
from scipy.signal import hilbert

def synthesize_phase_preserving(transfer, modal_response):
    H=np.asarray(transfer);q=np.asarray(modal_response)
    if H.ndim!=2 or q.ndim!=2 or H.shape[1]!=q.shape[0]:
        raise ValueError('Expected listener x mode transfer and mode x time response')
    if not np.isfinite(H).all() or not np.isfinite(q).all():
        raise ValueError('Nonfinite acoustic input')
    if np.iscomplexobj(q):raise ValueError('Modal response must be real')
    return np.real(H@hilbert(q,axis=1))
