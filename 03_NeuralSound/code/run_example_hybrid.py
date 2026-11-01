"""Apply the actual trained public vibration network to the author mesh.

Uses sparse matrices for the 17,898-DOF final LOBPCG, avoiding dense GPU storage.
Geometry is outside the local cuboid training family; errors remain explicit.
"""
import json,time,hashlib,argparse
import numpy as np
import torch
from scipy.sparse import load_npz
import train_vibration as local


def sparse(matrix):
    a=matrix.tocoo()
    return torch.sparse_coo_tensor(np.vstack((a.row,a.col)),a.data,a.shape,device='cuda',dtype=torch.float64).coalesce()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--iterations',type=int,default=2000)
    parser.add_argument('--extended',action='store_true')
    args=parser.parse_args()
    if args.iterations!=2000 and not args.extended:
        parser.error('Use --extended to preserve the original 2000-step experiment.')
    torch.set_num_threads(2);torch.set_grad_enabled(False)
    tag='example_hybrid_ood_extended' if args.extended else 'example_hybrid_ood'
    original=local.ROOT/'outputs/official_example';out=local.ROOT/'outputs'/tag;out.mkdir(parents=True,exist_ok=True)
    voxel=np.load(original/'voxel.npy');reference=np.load(original/'reference_modes.npz')
    K=load_npz(original/'stiffness.npz');M=load_npz(original/'mass.npz')
    official=local.official;official.device=torch.device('cuda:0');official.n=20;official.out_k=2
    model=local.Hexahedron_model(mat=local.Material.Ceramic)
    Ke=torch.tensor(model._element_stiff_matrix,device='cuda',dtype=torch.float32)
    Me=torch.tensor(model._element_mass_matrix,device='cuda',dtype=torch.float32)
    scaleK=float(torch.linalg.norm(Ke))*2;scaleM=float(torch.linalg.norm(Me))*2
    official.stiff_e=Ke/scaleK;official.mass_e=Me/scaleM
    A=sparse(K/scaleK);B=sparse(M/scaleM)
    edge=torch.tensor(local.voxel_to_edge(voxel),device='cuda',dtype=torch.long)
    coords=[torch.tensor(np.argwhere(voxel),dtype=torch.int32)]
    official.Config.net=local.defaultUnet(24,48,linear=True).cuda().eval()
    root_weights=local.ROOT/'outputs/vibration_training';records=[]
    for method in ('random','untrained_network','trained_network'):
        if method!='random':official.Config.net.load_state_dict(torch.load(root_weights/('best.pt' if method=='trained_network' else 'untrained.pt'),map_location='cpu'))
        torch.manual_seed(9010);torch.cuda.manual_seed_all(9010)
        X=torch.randn(K.shape[0],20,device='cuda');torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
        start=time.perf_counter()
        if method!='random':
            prediction=official.net(coords,X,edge)
            X,_=official.get_svqb(torch.cat((X,prediction),dim=1),edge)
        torch.cuda.synchronize();network_seconds=time.perf_counter()-start
        trace=[]
        def tracker(worker):
            if 'rerr' in worker.tvars:trace.append(float(worker.tvars['rerr'].max()))
        E,U=local.lobpcg(A,k=20,B=B,X=X.double(),niter=args.iterations,tol=1e-10,largest=False,tracker=tracker)
        torch.cuda.synchronize();total=time.perf_counter()-start
        E=E[6:].cpu().numpy()*scaleK/scaleM;U=U[:,6:].cpu().numpy()
        U/=np.sqrt(np.sum(U*(M@U),axis=0))
        rr=np.linalg.norm(K@U-(M@U)*E,axis=0)/(np.linalg.norm(K@U,axis=0)+np.linalg.norm((M@U)*E,axis=0))
        error=np.abs(E-reference['eigenvalues'][:14])/reference['eigenvalues'][:14]
        assert np.isfinite(E).all() and np.isfinite(U).all() and (E>0).all()
        np.savez_compressed(out/f'{method}.npz',eigenvalues=E,modes=U,relative_residuals=rr)
        record=dict(initialization=method,network_and_ritz_seconds=network_seconds,total_seconds=total,
            iterations=len(trace),max_eigenvalue_relative_error=float(error.max()),max_relative_residual=float(rr.max()),
            converged=bool(error.max()<1e-6 and rr.max()<1e-5),peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),trace=trace)
        records.append(record);print({k:v for k,v in record.items() if k!='trace'},flush=True)
        (out/'progress.json').write_text(json.dumps(records,indent=2))
    m=dict(scope='actual trained public defaultUnet on author example mesh with sparse strict refinement; geometry OOD',
        execution_completed=True,geometry_out_of_distribution=True,occupied_voxels=int(voxel.sum()),degrees_of_freedom=K.shape[0],
        elastic_modes=14,iteration_limit=args.iterations,extended_convergence_check=args.extended,
        records=records,checkpoint_sha256=hashlib.sha256((root_weights/'best.pt').read_bytes()).hexdigest(),
        limits=['trained on 24 cuboids, no tuning to this mesh','strict double precision sparse refinement differs from default float solver',
                'single raw timing per method, no paper speed claim','20-vector network includes six rigid modes, leaving fourteen elastic modes'])
    document_stem='example-hybrid-ood-extended' if args.extended else 'example-hybrid-ood'
    payload=json.dumps(m,indent=2);(out/'metrics.json').write_text(payload);(local.ROOT/'docs'/f'{document_stem}-metrics.json').write_text(payload)
    lines=['# 官方网格的实际神经振动混合求解','',
        '冻结已训练 defaultUnet，输入作者 example.obj 的 3863 体素网格。用稀疏 K/M 在 17,898 自由度上做原 LOBPCG 严格双精度精修，未为节省显存替换成小网格。此几何不属于长方体训练族。','']
    for r in records:lines.append(f'- {r["initialization"]}：{r["iterations"]} 次迭代，特征值最大相对误差 {r["max_eigenvalue_relative_error"]:.3g}，最大模态相对残差 {r["max_relative_residual"]:.3g}，收敛标记 {r["converged"]}。')
    lines+=['',f'迭代预算 {args.iterations}；'+('这是在原 2000 步未通过残差后增加预算的独立收敛诊断，原结果保持。未训练或调整网络。' if args.extended else '预先固定的初次预算。'),
        '',f'[完整指标]({document_stem}-metrics.json)。保存 14 个弹性模态；网络原设置 20 个向量包含六个刚体模态。计时包括网络初始化与求解，但只有一次原始测量，不作为论文性能。高精度来自数值精修，不全归因于网络。']
    (local.ROOT/'docs'/('EXAMPLE_HYBRID_OOD_EXTENDED.md' if args.extended else 'EXAMPLE_HYBRID_OOD.md')).write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':main()
