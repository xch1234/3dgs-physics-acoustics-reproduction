"""Constant-panel Helmholtz BEM with subdivided near-panel quadrature.

Retains the original indirect exterior-Neumann collocation formulation. Only
quadrature on nearby distinct panels changes; flat-panel self K' is zero.
"""
import numpy as np
from run_pat_extended import geometry,operator,pressure,BARY,QWEIGHT

def subdivided_rule(triangle,levels=2):
    triangles=np.asarray(triangle)[None]
    for _ in range(levels):
        a,b,c=triangles[:,0],triangles[:,1],triangles[:,2];ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
        triangles=np.concatenate([np.stack(v,1) for v in [(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]])
    area=np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)/2
    return np.einsum('qv,tvd->tqd',BARY,triangles).reshape(-1,3),(area[:,None]*QWEIGHT).ravel()

def accurate_operator(vertices,faces,k,near_radius=2.5,levels=2):
    mesh=geometry(vertices,faces);A=operator(mesh,k);center,normal,area,_=mesh
    # Correct near interactions at fixed geometry, not by altering the mesh/RHS.
    from scipy.spatial import cKDTree
    tree=cKDTree(center);corrected=0
    for j,tri in enumerate(vertices[faces]):
        ids=np.array(tree.query_ball_point(center[j],near_radius*np.sqrt(area[j])));ids=ids[ids!=j]
        if not len(ids):continue
        points,weights=subdivided_rule(tri,levels)
        delta=center[ids,None,:]-points[None,:,:];r=np.linalg.norm(delta,axis=2)
        dot=np.einsum('iqd,id->iq',delta,normal[ids]);kernel=np.exp(-1j*k*r)*(-1j*k*r-1)*dot/(4*np.pi*r**3)
        A[ids,j]=kernel@weights;corrected+=len(ids)
    return A,mesh,corrected
