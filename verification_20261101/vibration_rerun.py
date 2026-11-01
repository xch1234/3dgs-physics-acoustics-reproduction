"""Fresh frozen-network hybrid solves, checked per mode against reassembled FEM."""
import sys,time,json,gc,os
from common import ROOT,AUDIT,save
os.environ['NUMBA_CACHE_DIR']=str(AUDIT/'cache/numba')
sys.path.insert(0,str(ROOT/'03_NeuralSound/code'))
import train_vibration as m
import torch,numpy as np
from scipy.linalg import eigh
def main():
    torch.set_num_threads(2);torch.set_grad_enabled(False);device='cuda:0'
    m.official.device=torch.device(device);m.official.n=20;m.official.out_k=2
    m.official.Config.net=m.defaultUnet(24,48,linear=True).to(device)
    model=m.Hexahedron_model(mat=m.Material.Ceramic)
    Ke=torch.tensor(model._element_stiff_matrix,device=device,dtype=torch.float32);Me=torch.tensor(model._element_mass_matrix,device=device,dtype=torch.float32)
    m.official.stiff_e=Ke/torch.linalg.norm(Ke)/2;m.official.mass_e=Me/torch.linalg.norm(Me)/2
    samples=m.load_samples('test',device);records=[]
    for tag in ('vibration_training','vibration_paper_schedule'):
        folder=ROOT/'03_NeuralSound/outputs'/tag;out=AUDIT/'neural'/tag;out.mkdir(parents=True,exist_ok=True)
        m.official.Config.net.load_state_dict(torch.load(folder/'best.pt',map_location=device));m.official.Config.net.eval()
        score=m.validation(samples);save('neural/'+tag+'/network-validation.json',score)
        for i,s in enumerate(samples):
            physical=m.Hexahedron_model(s['data']['voxel'],m.Material.Ceramic)
            K=physical.stiff_matrix.toarray();M=physical.mass_matrix.toarray();reference=eigh(K,M,subset_by_index=(0,19),eigvals_only=True)
            A=torch.tensor(K/(float(torch.linalg.norm(Ke))*2),device=device,dtype=torch.float64);B=torch.tensor(M/(float(torch.linalg.norm(Me))*2),device=device,dtype=torch.float64)
            torch.manual_seed(9000+i);torch.cuda.manual_seed_all(9000+i)
            initial=torch.randn(s['vertices']*3,20,device=device)
            predicted=m.official.net(s['coords'],initial,s['edge']);initial,_=m.official.get_svqb(torch.cat((initial,predicted),dim=1),s['edge'])
            t=time.monotonic();E,U=m.lobpcg(A,k=20,B=B,X=initial.double(),niter=2000,tol=1e-10,largest=False);torch.cuda.synchronize();elapsed=time.monotonic()-t
            u=U.cpu().numpy();elastic=u[:,6:];ku=K@elastic;mu=M@elastic;rq=np.sum(elastic*ku,axis=0)/np.sum(elastic*mu,axis=0)
            residual=np.linalg.norm(ku-mu*rq,axis=0)/(np.linalg.norm(ku,axis=0)+np.linalg.norm(mu*rq,axis=0));error=float(np.max(abs(rq/reference[6:20]-1)))
            row=dict(run=tag,sample=s['name'],max_elastic_residual=float(residual.max()),max_elastic_eigenvalue_error=error,elapsed_s=elapsed,passed=bool(residual.max()<1e-6 and error<1e-6))
            records.append(row);np.savez_compressed(out/(s['name'].replace('.npz','')+'_fresh_modes.npz'),modes=u,physical_eigenvalues=rq,reference=reference)
            print(row,flush=True)
        save('neural/vibration-fresh-solves.json',records)
    assert all(r['passed'] for r in records)
if __name__=='__main__':main()
