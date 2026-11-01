"""Saved vibration model: include network and Ritz costs in hybrid timings."""
import os
os.environ['OMP_NUM_THREADS']='2'
import json,time
import numpy as np
import torch
from scipy.linalg import eigh
import train_vibration as local


def main():
    torch.set_num_threads(2);torch.set_grad_enabled(False)
    official=local.official;official.device=torch.device('cuda:0');official.n=20;official.out_k=2
    official.Config.net=local.defaultUnet(24,48,linear=True).cuda().eval()
    element=local.Hexahedron_model(mat=local.Material.Ceramic)
    Ke=torch.tensor(element._element_stiff_matrix,device='cuda',dtype=torch.float32)
    Me=torch.tensor(element._element_mass_matrix,device='cuda',dtype=torch.float32)
    scaleK=float(torch.linalg.norm(Ke))*2;scaleM=float(torch.linalg.norm(Me))*2
    official.stiff_e=Ke/scaleK;official.mass_e=Me/scaleM
    folder=local.ROOT/'outputs/vibration_training';records=[]
    best=torch.load(folder/'best.pt',map_location='cpu')
    untrained=torch.load(folder/'untrained.pt',map_location='cpu')
    for j,sample in enumerate(local.load_samples('test','cuda:0')):
        model=local.Hexahedron_model(sample['data']['voxel'],local.Material.Ceramic)
        A=torch.tensor(model.stiff_matrix.toarray()/scaleK,device='cuda',dtype=torch.float64)
        B=torch.tensor(model.mass_matrix.toarray()/scaleM,device='cuda',dtype=torch.float64)
        reference=eigh(A.cpu().numpy(),B.cpu().numpy(),subset_by_index=(0,19),eigvals_only=True)
        for method in ('random','untrained_network','trained_network'):
            if method!='random':official.Config.net.load_state_dict(best if method=='trained_network' else untrained)
            trials=[]
            for repeat in range(4):
                torch.manual_seed(9000+j);torch.cuda.manual_seed_all(9000+j)
                x0=torch.randn(sample['vertices']*3,20,device='cuda')
                torch.cuda.synchronize();start=time.perf_counter()
                if method!='random':
                    predicted=official.net(sample['coords'],x0,sample['edge'])
                    x0,_=official.get_svqb(torch.cat((x0,predicted),dim=1),sample['edge'])
                torch.cuda.synchronize();after_network=time.perf_counter()
                E,U=local.lobpcg(A,k=20,B=B,X=x0.double(),niter=2000,tol=1e-10,largest=False)
                torch.cuda.synchronize();finish=time.perf_counter()
                error=float(np.max(np.abs(E[6:12].cpu().numpy()-reference[6:12])/reference[6:12]))
                residual=float(torch.linalg.norm(A@U-B@U*E)/(torch.linalg.norm(A@U)+torch.linalg.norm(B@U*E)))
                assert error<1e-7 and residual<1e-7,(sample['name'],method,error,residual)
                row=dict(network_and_ritz_seconds=after_network-start,solver_seconds=finish-after_network,
                    total_seconds=finish-start,first_six_eigenvalue_max_relative_error=error,relative_residual=residual)
                if repeat:trials.append(row)  # One untimed-in-report warmup per configuration.
            record=dict(sample=sample['name'],method=method,trials=trials,
                median_total_seconds=float(np.median([r['total_seconds'] for r in trials])),
                median_network_and_ritz_seconds=float(np.median([r['network_and_ritz_seconds'] for r in trials])))
            records.append(record);print(record,flush=True)
    ratios=[]
    for j in range(0,len(records),3):
        ratios.append(dict(sample=records[j]['sample'],random_over_trained=records[j]['median_total_seconds']/records[j+2]['median_total_seconds']))
    m=dict(scope='local small dense refinement, including actual neural initialization; not paper speed benchmark',
        all_checks_passed=True,warmup_trials=1,measured_trials=3,records=records,observed_ratios=ratios,
        limits=['four local held-out cuboids','no FEM assembly, data-loading, model construction or checkpoint IO in timings',
                'dense matrices in final strict double precision refinement','single laptop, not original paper hardware'])
    payload=json.dumps(m,indent=2);(folder/'benchmark.json').write_text(payload)
    (local.ROOT/'docs/vibration-benchmark.json').write_text(payload)
    lines=['# 振动混合求解完整计算阶段计时','',
        '固定已训练权重和独立测试物体，每种配置预热一次、测量三次。计时包含网络前向、SVQB/Rayleigh–Ritz 初始化和相同严格 LOBPCG 求解；不包括模型载入、矩阵组装和文件 I/O。',
        '所有计时样本均重新检查特征值误差与残差，保持统一容差。小对象使用稠密双精度最终精修，不是论文原始稀疏大模型速度基准。','']
    for row in ratios:lines.append(f'- {row["sample"]}：随机初始化总时间 / 已训练混合总时间 = {row["random_over_trained"]:.3f}。')
    lines+=['','[全部原始计时](vibration-benchmark.json)。该比值只描述这次本地实验；训练成本不包含在推理计时中。']
    (local.ROOT/'docs/VIBRATION_BENCHMARK.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':main()
