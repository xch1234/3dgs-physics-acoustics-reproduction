"""Prespecified OOD radiation test on the original author mesh's first two modes.

Prepare BEM on CPU, then evaluate the frozen locally trained AcousticNet on GPU.
The first two original Ceramic modes lie inside the local training frequencies;
the mesh geometry is completely outside the cuboid training family.
"""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[key]='2'
import sys,json,time,argparse,hashlib
from pathlib import Path
import numpy as np
for key,value in {'bool':bool,'int':int,'float':float,'complex':complex}.items():
    if key not in np.__dict__:setattr(np,key,value)
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'code/NeuralSound'))


def prepare():
    from scipy.sparse import load_npz
    import bempp.api.linalg
    from bempp.api.operators import boundary,potential
    from src.classic.bem import ffat
    from src.classic.bem.util import boundary_voxel,boundary_encode
    from src.classic.fem.util import vertex_to_voxel_matrix
    source=ROOT/'outputs/official_example';out=ROOT/'inputs/official_example_acoustic';out.mkdir(parents=True,exist_ok=True)
    if (out/'reference-metrics.json').exists():
        print('Verified reference already saved.',flush=True);return
    voxel=np.load(source/'voxel.npy');modal=np.load(source/'reference_modes.npz')
    U=modal['modes'][:,:2].copy();E=modal['eigenvalues'][:2]
    K=load_npz(source/'stiffness.npz');M=load_npz(source/'mass.npz')
    U/=np.sqrt(np.sum(U*(M@U),axis=0))
    residual=np.linalg.norm(K@U-(M@U)*E,axis=0)/(np.linalg.norm(K@U,axis=0)+np.linalg.norm((M@U)*E,axis=0))
    assert residual.max()<1e-6
    frequencies=np.sqrt(E)/(2*np.pi);assert np.all((frequencies>300)&(frequencies<6000))
    coords=np.argwhere(voxel);vib=(vertex_to_voxel_matrix(voxel)@U.reshape(-1,6)).reshape(len(coords),3,2)
    surface,index=map(np.asarray,boundary_voxel(coords))
    original_boundary=ffat.voxel2boundary
    def integer_boundary(*a,**kw):
        v,f,i=original_boundary(*a,**kw);return np.asarray(v),np.asarray(f,dtype=np.int64),np.asarray(i,dtype=np.int64)
    ffat.voxel2boundary=integer_boundary
    for module,names in ((boundary.helmholtz,('adjoint_double_layer','hypersingular')),
                         (boundary.sparse,('identity',)),(potential.helmholtz,('single_layer','double_layer'))):
        for name in names:
            original=getattr(module,name)
            def cpu_double(*a,_original=original,**kw):
                kw['device_interface']='numba';kw['precision']='double';return _original(*a,**kw)
            setattr(module,name,cpu_double)
    original_gmres=bempp.api.linalg.gmres;solves=[]
    def checked(A,b,**kw):
        kw['tol']=1e-8;result=original_gmres(A,b,**kw);rhs=b.projections(A.dual_to_range)
        weak=A.weak_form()
        rr=float(np.linalg.norm(weak@result[0].coefficients-rhs)/np.linalg.norm(rhs))
        attempt=dict(info=int(result[1]),relative_residual=rr,iterations=len(result[2]))
        row=dict(method='GMRES',info=int(result[1]),relative_residual=rr,gmres_attempt=attempt)
        if result[1]!=0 or rr>=1.01e-8:
            # Preserve the failed iteration; solve the SAME assembled equation.
            # Dense LU is affordable for this single ~4k boundary-vertex mesh.
            from scipy.linalg import solve
            matrix=weak.to_dense();index=len(solves)
            np.savez_compressed(out/f'boundary_system_{index}.npz',matrix=matrix,rhs=rhs,
                gmres_coefficients=result[0].coefficients)
            print('GMRES failed strict residual; direct LU fallback:',attempt,flush=True)
            coefficients=solve(matrix,rhs,assume_a='gen',check_finite=True)
            rr=float(np.linalg.norm(matrix@coefficients-rhs)/np.linalg.norm(rhs))
            function=bempp.api.GridFunction(A.domain,coefficients=coefficients)
            result=(function,0,result[2])
            row.update(method='SciPy dense LU on identical Bempp weak form',info=0,relative_residual=rr)
            np.save(out/f'direct_coefficients_{index}.npy',coefficients)
        solves.append(row)
        (out/'solve-progress.json').write_text(json.dumps(solves,indent=2))
        print('SOLVE',row,flush=True)
        assert result[1]==0 and rr<1.01e-8,row
        return result
    bempp.api.linalg.gmres=checked
    print('ORIGINAL EXAMPLE: 3863 voxels, 8144 surface triangles, first two physical modes',flush=True)
    start=time.perf_counter();near,far=ffat.vibration_to_ffat(coords,vib,frequencies)
    assert np.isfinite(far).all() and len(solves)==2
    np.savez_compressed(out/'example.npz',voxel=voxel,coords=surface,feats_in=vib[index],surface=np.asarray(boundary_encode(surface)),
        feats_out=near,feats_out_far=far,freqs=frequencies)
    (out/'test.txt').write_text('example.npz\n')
    record=dict(scope='original author example geometry, first two modes of independent Ceramic FEM reference',
        reference_checks_passed=True,frequencies_Hz=frequencies.tolist(),modal_relative_residuals=residual.tolist(),
        bem_solves=solves,elapsed_s=time.perf_counter()-start,occupied_voxels=int(voxel.sum()),surface_triangles=8144,
        adaptation='GMRES failure retained; if needed dense LU solves the identical assembled weak equation without relaxing residual tolerance')
    (out/'reference-metrics.json').write_text(json.dumps(record,indent=2));print(record,flush=True)


def predict(device='cuda:0'):
    import torch
    from torch.utils.data import DataLoader
    from train_radiation import Maps,collate,AcousticNet,evaluate
    torch.set_num_threads(2);torch.set_grad_enabled(False)
    source=ROOT/'inputs/official_example_acoustic';reference=json.loads((source/'reference-metrics.json').read_text())
    assert reference['reference_checks_passed']
    out=ROOT/'outputs/example_acoustic_ood';out.mkdir(parents=True,exist_ok=True)
    network=AcousticNet(23).to(device).eval();weights=ROOT/'outputs/radiation_training/best.pt'
    saved=torch.load(weights,map_location='cpu');network.load_state_dict(saved['model']);del saved
    loader=DataLoader(Maps('test',False,source),batch_size=1,collate_fn=collate,num_workers=0)
    results=evaluate(network,loader,device,save=out/'maps.png')
    cpu_gpu_check=None
    if device=='cpu':
        from torch.utils.data import Subset
        check_loader=DataLoader(Subset(Maps('test',False),[0,1]),batch_size=2,collate_fn=collate,num_workers=0)
        cpu=evaluate(network,check_loader,'cpu')
        gpu=json.loads((ROOT/'outputs/radiation_training/metrics.json').read_text())['test']['samples'][:2]
        differences=[]
        for c,g in zip(cpu['samples'],gpu):
            assert c['sample']==g['sample']
            differences.extend(abs(c[k]-g[k]) for k in ('normalized_map_relative_L2','amplitude_log_error','transfer_relative_L2'))
        assert max(differences)<1e-4,differences
        cpu_gpu_check=dict(samples=cpu['samples'],maximum_absolute_metric_difference=max(differences),passed=True,
            scope='same frozen network and batch of two local test maps against saved GPU metrics; no weight adjustment')
    m=dict(scope='frozen locally trained public AcousticNet on original author example mesh',execution_completed=True,
        inference_device=device,cpu_gpu_consistency=cpu_gpu_check,
        geometry_out_of_distribution=True,within_training_frequency_range=True,mode_selection='first two original Ceramic modes, fixed before training completed',
        reference=reference,test=results,checkpoint_sha256=hashlib.sha256(weights.read_bytes()).hexdigest(),
        limits=['network trained only on cuboids; no tuning to example','uses independent reference FEM modes for isolated radiation evaluation',
                'two in-range modes only; not all modes or ABC benchmark'])
    payload=json.dumps(m,indent=2);(out/'metrics.json').write_text(payload);(ROOT/'docs/example-acoustic-ood-metrics.json').write_text(payload)
    report=f'''# 官方网格的声辐射泛化检查

在完成网络训练前固定测试作者 example.obj 的前两个 Ceramic 模态（{', '.join(f'{f:.2f}' for f in reference['frequencies_Hz'])} Hz），其频率位于本地增强范围，但几何不属于训练长方体族。3863 体素、8144 表面三角面；官方 Bempp 双精度/Numba 算子生成独立参考并检查显式残差。首次 GMRES 500 次后残差 2.35e-5，未达标；失败日志保留。最终参考允许在 GMRES 失败时对同一组装矩阵使用 SciPy 直接 LU，不放宽 1e-8 容差；实际方法和两次原始 GMRES 结果记录在指标中。对应矩阵、右端项、失败迭代系数和直接解均保存。

冻结已训练公开 AcousticNet，未用此物体选择权重或调参。两张 FFAT 的平均相对 L2 为 **{results['mean_transfer_relative_L2']*100:.3f}%**。这项指标直接反映局部简单数据的泛化局限，不以能生成预测图代替精度达标。

本次推理设备为 `{device}`。曾尝试 CPU，但 MinkowskiEngine 的全局池化在此输入触发 `Invalid out_coordinate_map` 断言，失败日志为 `logs/example-radiation-ood-cpu.log`；不能把 CPU 尝试称为成功。本次 CUDA 推理前实测空闲显存约 2519 MiB，而已运行同网络单样本推理峰值约 1.26 GB，因此与较低显存的 Wolf 模拟并行调度；不使用此次墙钟宣称推理速度。

[指标与参考审计](example-acoustic-ood-metrics.json) · [真实参考/预测图](../outputs/example_acoustic_ood/maps.png)。参考保存在 inputs/official_example_acoustic。本测试使用独立 FEM 模态以单独评估声辐射，并非此网格上的神经振动端到端结果。

先在 Linux NeuralSound Conda 运行 `python code/run_example_acoustics.py --prepare`，然后使用 CUDA 运行 `--predict`。保留的 `--device cpu` 仅用于重现上述失败，不是此输入的可用替代入口。大网格 BEM 与训练同时运行可能超过内存；参考 elapsed_s 包含约 1.5 分钟为独立计时而暂停的调度，不能当论文性能。
'''
    (ROOT/'docs/EXAMPLE_ACOUSTIC_OOD.md').write_text(report,encoding='utf-8');print(payload,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--predict',action='store_true');p.add_argument('--device',choices=['cpu','cuda:0'],default='cuda:0');a=p.parse_args()
    if a.prepare:prepare()
    if a.predict:predict(a.device)
    if not (a.prepare or a.predict):p.error('Choose --prepare and/or --predict')
