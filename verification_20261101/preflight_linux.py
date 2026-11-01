import sys,os,importlib,json
from common import run,runtime_env,save
def main():
    rows=[]
    for name in ('physgaussian','neuralsound','pat-tools'):
        prefix='/opt/3dgs-runtime/envs/'+name;env=runtime_env(prefix)
        rows.append(run('env-'+name+'-pip',[prefix+'/bin/python','-m','pip','check'],env=env,required=False))
        packages=['numpy','scipy','torch','warp','taichi','diff_gaussian_rasterization','simple_knn._C'] if name=='physgaussian' else ['numpy','scipy','torch','MinkowskiEngine','torch_scatter','pycuda.driver','bempp.api'] if name=='neuralsound' else ['numpy']
        code='import importlib,json; modules='+repr(packages)+'; result={}\nfor name in modules:\n m=importlib.import_module(name); result[name]={"version":str(getattr(m,"__version__",None)),"file":str(getattr(m,"__file__",None))}\n'
        if name!='pat-tools':code+='import torch\na=torch.arange(16,device="cuda",dtype=torch.float32).reshape(4,4); b=a@a.T; torch.cuda.synchronize(); assert torch.isfinite(b).all();result["cuda"]={"available":torch.cuda.is_available(),"device":torch.cuda.get_device_name(0),"torch_cuda":torch.version.cuda,"matmul":b.cpu().tolist()}\n'
        code+='print(json.dumps(result,indent=2))'
        rows.append(run('env-'+name+'-imports',[prefix+'/bin/python','-c',code],env=env,required=False))
    for name,command in [('nvcc',['/opt/3dgs-runtime/envs/physgaussian/bin/nvcc','--version']),('gpp',['g++','--version']),('linux-memory',['free','-h']),('linux-gpu',['nvidia-smi'])]:rows.append(run(name,command,required=False))
    save('environment-linux.json',rows)
if __name__=='__main__':main()
