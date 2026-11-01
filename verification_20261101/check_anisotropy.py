import ast,json,sys
import numpy as np,torch
from plyfile import PlyData
from common import ROOT,AUDIT,save,digest

def main():
    torch.set_num_threads(2)
    source=ROOT/'01_PhysGaussian/code/train_with_anisotropy.py'
    node=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='anisotropy_loss')
    ns={'torch':torch};exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),ns);loss=ns['anisotropy_loss']
    rng=np.random.default_rng(33);scales=np.exp(rng.normal(size=(50,3)));threshold=3.
    t=torch.tensor(scales,dtype=torch.float64,requires_grad=True);value=loss(t,threshold);value.backward()
    ratios=scales.max(1)/scales.min(1);reference=np.maximum(ratios-threshold,0).mean();expected=np.zeros_like(scales)
    for i,s in enumerate(scales):
        if ratios[i]>threshold:
            expected[i,s.argmax()]=1/s.min()/len(scales)
            expected[i,s.argmin()]=-s.max()/s.min()**2/len(scales)
    np.testing.assert_allclose(float(value),reference,rtol=1e-13);np.testing.assert_allclose(t.grad.numpy(),expected,rtol=1e-13,atol=1e-13)
    assert torch.autograd.gradcheck(lambda x:loss(x,threshold),(t,),eps=1e-6,atol=1e-6)
    np.testing.assert_allclose(float(loss(t*8,threshold)),reference,rtol=1e-13)
    rows=[]
    for tag in ('ficus_reconstruction','ficus_anisotropy'):
        folder=ROOT/'01_PhysGaussian/outputs'/tag;path=folder/'point_cloud/iteration_30000/point_cloud.ply'
        p=PlyData.read(str(path))['vertex'].data
        scales=np.column_stack([p['scale_'+str(i)] for i in range(3)]).astype(float)
        assert np.isfinite(scales).all();ratio=np.exp(scales.max(1)-scales.min(1))
        rows.append(dict(model=tag,particles=len(p),mean_ratio=float(ratio.mean()),maximum_ratio=float(ratio.max()),fraction_over_5=float((ratio>5).mean()),penalty_above_5=float(np.maximum(ratio-5,0).mean()),sha256=digest(path)))
    save('checks/anisotropy.json',dict(function_test_passed=True,analytic_gradient_max_error=float(abs(t.grad.numpy()-expected).max()),source_sha256=digest(source),saved_PLY_readback=rows,limitation='Fresh CPU loss/gradient tests and stored PLY measurement only; no fresh 30000-step regularized training or ablation benchmark.'))
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
