"""External AST adapter adds PhysGaussian Eq.(12) to the pinned 3DGS trainer.

The upstream file remains unchanged. The experiment is a documented local
regularization control, since the paper does not specify a reproducible r/lambda.
"""
import os
import sys
import ast
import json
import argparse
import hashlib
from pathlib import Path
import torch

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT/'code/PhysGaussian/gaussian-splatting'


def anisotropy_loss(scales,threshold):
    # Parameterization is exponential, so scales are strictly positive.
    ratio=scales.amax(dim=1)/scales.amin(dim=1)
    return (ratio-threshold).clamp_min(0).mean()


def self_check():
    scales=torch.tensor([[1.,2.,6.],[2.,2.5,3.],[1.,4.,2.]],dtype=torch.float64,requires_grad=True)
    loss=anisotropy_loss(scales,3.);assert abs(float(loss)-4/3)<1e-12
    loss.backward();analytic=scales.grad.clone();numerical=torch.zeros_like(scales)
    for i in range(3):
        for j in range(3):
            a=scales.detach().clone();b=a.clone();a[i,j]+=1e-6;b[i,j]-=1e-6
            numerical[i,j]=(anisotropy_loss(a,3.)-anisotropy_loss(b,3.))/(2e-6)
    error=float(torch.max(torch.abs(analytic-numerical)));assert error<1e-8
    assert torch.equal(analytic[1],torch.zeros(3,dtype=torch.float64))
    assert abs(float(anisotropy_loss(scales.detach()*7.,3.))-float(loss))<1e-12
    assert float(anisotropy_loss(torch.ones(4,3,dtype=torch.float64),3.))==0
    report=dict(passed=True,reference_loss=4/3,actual_loss=float(loss),finite_difference_max_absolute_error=error,
        checks=['known piecewise loss','zero inactive gradients','finite-difference active gradients','uniform-scale invariance','isotropic zero penalty'])
    (ROOT/'docs/anisotropy-function-check.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--aniso-threshold',type=float,default=5.)
    parser.add_argument('--aniso-weight',type=float,default=.01)
    parser.add_argument('--self-check',action='store_true')
    args,upstream_args=parser.parse_known_args()
    if args.self_check:self_check();return
    assert args.aniso_threshold>1 and args.aniso_weight>0
    out=ROOT/'outputs/ficus_anisotropy';out.mkdir(parents=True,exist_ok=True)
    source=(REPO/'train.py').read_text(encoding='utf-8')
    tree=ast.parse(source);insertions=[];history=[]
    class AddLoss(ast.NodeTransformer):
        def visit_Assign(self,node):
            if len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='loss':
                insertions.append(node.lineno)
                node.value=ast.Call(func=ast.Name(id='add_anisotropy_loss',ctx=ast.Load()),
                    args=[node.value,ast.Name(id='gaussians',ctx=ast.Load()),ast.Name(id='iteration',ctx=ast.Load())],keywords=[])
            return self.generic_visit(node)
    tree=AddLoss().visit(tree);ast.fix_missing_locations(tree)
    assert len(insertions)==1,insertions
    protocol=dict(source_train_sha256=hashlib.sha256(source.encode()).hexdigest(),loss_line=insertions[0],
        threshold=args.aniso_threshold,weight=args.aniso_weight,upstream_arguments=upstream_args,
        adaptation='Only the photometric loss assignment is wrapped to add weighted Eq.(12); original source file unchanged.')
    (out/'adapter-protocol.json').write_text(json.dumps(protocol,indent=2))
    def add_loss(photo,gaussians,iteration):
        scales=gaussians.get_scaling
        penalty=anisotropy_loss(scales,args.aniso_threshold)
        assert torch.isfinite(penalty)
        if iteration==1 or iteration%1000==0:
            with torch.no_grad():
                ratio=scales.amax(dim=1)/scales.amin(dim=1)
                row=dict(iteration=iteration,particles=len(scales),photometric_loss=float(photo),
                    anisotropy_loss=float(penalty),mean_axis_ratio=float(ratio.mean()),
                    fraction_above_threshold=float((ratio>args.aniso_threshold).float().mean()),max_axis_ratio=float(ratio.max()))
                history.append(row);(out/'anisotropy-history.json').write_text(json.dumps(history,indent=2))
                print('ANISOTROPY',row,flush=True)
        return photo+args.aniso_weight*penalty
    os.chdir(REPO);sys.path.insert(0,str(REPO))
    sys.argv=[str(REPO/'train.py'),*upstream_args]
    scope={'__name__':'__main__','__file__':str(REPO/'train.py'),'add_anisotropy_loss':add_loss}
    exec(compile(tree,str(REPO/'train.py'),'exec'),scope)


if __name__=='__main__':main()
