from pathlib import Path
import sys,json,time
import numpy as np
from scipy.linalg import solve
from scipy.spatial import ConvexHull
R=Path(__file__).resolve().parents[1];A=R/'remediation_20261101';sys.path.insert(0,str(R/'02_PAT/code'))
from bem_near_quadrature import accurate_operator,pressure
from run_pat import refine,sphere_points,hankel
out=A/'bem_convergence';out.mkdir(exist_ok=True);radius=.05;g=(1+np.sqrt(5))/2
v=np.array([(0,a,b*g) for a in (-1,1) for b in (-1,1)]+[(a,b*g,0) for a in (-1,1) for b in (-1,1)]+[(b*g,0,a) for a in (-1,1) for b in (-1,1)],float);v*=radius/np.linalg.norm(v[0]);f=ConvexHull(v).simplices;k=2*np.pi*400/343;query=sphere_points(96,.3);exact=np.full(len(query),hankel(0,k*.3)/(k*hankel(0,k*radius,True)));rows=[]
for level in range(1,5):
 v,f,_=refine(v,f,radius=radius);start=time.time();mat,mesh,n=accurate_operator(v,f,k);sigma=solve(mat,np.ones(len(f)),check_finite=False);p=pressure(query,mesh,k,sigma)
 row={'triangles':len(f),'relative_complex_error':float(np.linalg.norm(p-exact)/np.linalg.norm(exact)),'linear_residual':float(np.linalg.norm(mat@sigma-1)/np.sqrt(len(f))),'near_pairs':n,'seconds':time.time()-start};rows.append(row);print(row,flush=True);(out/'progress.json').write_text(json.dumps(rows,indent=2));np.savez_compressed(out/f'panels_{len(f)}.npz',pressure=p,reference=exact,queries=query)
result={'scope':'local pulsating-sphere discretization experiment only; not all PAT paper scenes/high-frequency/7000x benchmark','rows':rows,'monotonic':all(a['relative_complex_error']>b['relative_complex_error'] for a,b in zip(rows,rows[1:])),'finest_below_half_percent':rows[-1]['relative_complex_error']<.005}
(A/'checks/V09-convergence.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
