"""CPU metamorphic check of original SH function across preprocessing frames.

Extract the unchanged function AST to avoid importing the CUDA-only renderer.
This validates the actual SH function, not rasterization or a full simulation.
"""
import ast,json,hashlib,importlib.util
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from sh_frame_adapter import inverse_rotation_to_world

ROOT=Path(__file__).resolve().parents[1];REPO=ROOT/'code/PhysGaussian'


def rotation(axis,angle):
    a=np.eye(3);u=(axis+1)%3;v=(axis+2)%3
    a[u,u]=a[v,v]=np.cos(angle);a[u,v]=-np.sin(angle);a[v,u]=np.sin(angle)
    return torch.tensor(a,dtype=torch.float64)


def main():
    torch.set_num_threads(2);torch.set_grad_enabled(False);torch.manual_seed(20261104)
    source=REPO/'utils/render_utils.py';nodes=ast.parse(source.read_text()).body
    fn=next(n for n in nodes if isinstance(n,ast.FunctionDef) and n.name=='convert_SH')
    spec=importlib.util.spec_from_file_location('published_sh',REPO/'gaussian-splatting/utils/sh_utils.py')
    sh=importlib.util.module_from_spec(spec);spec.loader.exec_module(sh)
    namespace=dict(torch=torch,GaussianModel=object,eval_sh=sh.eval_sh)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),namespace)
    convert=namespace['convert_SH'];pc=SimpleNamespace(active_sh_degree=3,max_sh_degree=3)
    positions=torch.randn(48,3,dtype=torch.float64);camera=torch.tensor([3.,2.,4.],dtype=torch.float64)
    coefficients=torch.randn(48,16,3,dtype=torch.float64)*.04
    baseline=convert(coefficients,SimpleNamespace(camera_center=camera),pc,positions)
    W=rotation(2,.63)@rotation(0,.27);offset=torch.tensor([.3,-.2,.1],dtype=torch.float64)
    moved=positions@W.T+offset;moved_camera=W@camera+offset
    cases=[('identity',[torch.eye(3,dtype=torch.float64)]),('x90',[rotation(0,np.pi/2)]),
        ('composed',[rotation(0,.7),rotation(1,-.4),rotation(2,.2)])]
    records=[];arrays={}
    for name,pre in cases:
        Q=torch.eye(3,dtype=torch.float64)
        for r in pre:Q=r@Q
        F_mpm=Q@W@Q.T
        inverse_mpm=F_mpm.T[None].repeat(len(positions),1,1)
        original=convert(coefficients,SimpleNamespace(camera_center=moved_camera),pc,moved,inverse_mpm)
        corrected=convert(coefficients,SimpleNamespace(camera_center=moved_camera),pc,moved,
            inverse_rotation_to_world(inverse_mpm,pre))
        error=lambda a:float(torch.linalg.norm(a-baseline)/torch.linalg.norm(baseline))
        row=dict(case=name,original_color_relative_L2=error(original),corrected_color_relative_L2=error(corrected))
        assert row['corrected_color_relative_L2']<1e-12,row
        if name=='identity':assert row['original_color_relative_L2']<1e-12
        else:assert row['original_color_relative_L2']>1e-3,row
        records.append(row);arrays[name+'_original']=original.numpy();arrays[name+'_corrected']=corrected.numpy()
    out=ROOT/'outputs/sh_frame_audit';out.mkdir(exist_ok=True)
    np.savez_compressed(out/'color_reference.npz',baseline=baseline.numpy(),**arrays)
    result=dict(execution_completed=True,adapter_checks_passed=True,upstream_nonidentity_frame_invariance_passed=False,
        records=records,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        conclusion='The released gs_simulation restores positions/covariances to world space but passes the MPM-basis inverse rotation directly to world-space SH view directions. Conjugation Q.T @ R_inverse @ Q fixes the noncommuting-frame case.',
        scope='original convert_SH function on CPU plus an external basis-conversion adapter; no claim that previous full-scene videos used this correction')
    payload=json.dumps(result,indent=2);(out/'metrics.json').write_text(payload);(ROOT/'docs/sh-frame-metrics.json').write_text(payload)
    lines='\n'.join(f'- {r["case"]}：原函数路径相对颜色误差 {r["original_color_relative_L2"]:.6g}；坐标变换适配后 {r["corrected_color_relative_L2"]:.3g}。' for r in records)
    report=f'''# SH 旋转坐标系审计与外部修复

复查发现一个原实现边界：gs_simulation.py 将粒子位置和协方差从 MPM 坐标变回世界坐标，但传给 convert_SH 的逆旋转仍处于 MPM 坐标。若预旋转 Q 非单位阵且不与物体旋转交换，应使用 Qᵀ R_mpm⁻¹ Q。Ficus 的 Q=I 不受此问题影响。

本实验从原文件提取未改动的 convert_SH 函数 AST，在 CPU 调用原 eval_sh，构造 48 组固定三阶 SH 和同步旋转的物体/相机。世界坐标变换不应改变材料相对视线，因此颜色应保持。三种预旋转的实测为：

{lines}

原实现的非单位坐标系测试失败已保留。仓库外 sh_frame_adapter.py 的坐标共轭修复通过；完整运行包装器新增可选 --correct-sh-frame 开关。原六场景视频仍是未修复的发布代码结果，不覆盖、不改写旧数值；不能把本模块修复测试宣称为所有场景修复版已重新运行。

此检查独立于 CUDA 光栅器，只验证 SH 颜色与坐标系不变量。原极分解输出的单精度误差另外见 [输运审计](GAUSSIAN_TRANSPORT.md)。[机器指标](sh-frame-metrics.json) · [参考颜色](../outputs/sh_frame_audit/color_reference.npz)。
'''
    (ROOT/'docs/SH_FRAME_AUDIT.md').write_text(report,encoding='utf-8');print(payload,flush=True)


if __name__=='__main__':main()
