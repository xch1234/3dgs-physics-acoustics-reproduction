"""Adam with CPU-resident moments for training the full network on a 4 GiB GPU.

Updates use float32 CPU arithmetic and retain an exact CPU parameter copy.
Pinned transfer buffers avoid copying the same GPU parameters back each step.
No model layers are reduced; host updates trade speed for GPU memory.
"""
import math
import torch


class CPUAdam(torch.optim.Optimizer):
    def __init__(self,params,lr=1e-3,betas=(.9,.999),eps=1e-8):
        super().__init__(params,dict(lr=lr,betas=betas,eps=eps))
        self._transfer_buffer=None
    @torch.no_grad()
    def step(self,closure=None):
        loss=None
        if closure is not None:
            with torch.enable_grad():loss=closure()
        for group in self.param_groups:
            b1,b2=group['betas']
            for p in group['params']:
                if p.grad is None:continue
                state=self.state[p]
                if not state:
                    state.update(step=0,exp_avg=torch.zeros_like(p,device='cpu'),exp_avg_sq=torch.zeros_like(p,device='cpu'))
                if 'master_param' not in state:
                    state['master_param']=torch.empty_like(p,device='cpu',pin_memory=p.is_cuda)
                    state['master_param'].copy_(p.detach())
                if p.is_cuda:
                    if self._transfer_buffer is None or self._transfer_buffer.numel()<p.numel():
                        self._transfer_buffer=torch.empty(p.numel(),dtype=p.dtype,device='cpu',pin_memory=True)
                    grad=self._transfer_buffer[:p.numel()].view_as(p)
                    grad.copy_(p.grad.detach(),non_blocking=True)
                    torch.cuda.current_stream(p.device).synchronize()
                else:grad=p.grad.detach()
                state['step']+=1;t=state['step']
                m,v=state['exp_avg'],state['exp_avg_sq']
                m.mul_(b1).add_(grad,alpha=1-b1);v.mul_(b2).addcmul_(grad,grad,value=1-b2)
                denominator=v.sqrt().div_(math.sqrt(1-b2**t)).add_(group['eps'])
                value=state['master_param']
                value.addcdiv_(m,denominator,value=-group['lr']/(1-b1**t))
                p.copy_(value)
        return loss
    def load_state_dict(self,packed):
        # Base Optimizer would move all moments onto the parameter's CUDA device.
        for current,saved in zip(self.param_groups,packed['param_groups']):
            for key,value in saved.items():
                if key!='params':current[key]=value
            for param,index in zip(current['params'],saved['params']):
                if index in packed['state']:
                    self.state[param]={k:v.cpu() if torch.is_tensor(v) else v for k,v in packed['state'][index].items()}
                    if param.is_cuda and 'master_param' in self.state[param]:
                        self.state[param]['master_param']=self.state[param]['master_param'].pin_memory()

    def model_state_dict(self,model):
        """CPU checkpoint with storage shared with optimizer master parameters."""
        named=dict(model.named_parameters())
        result={}
        for name,tensor in model.state_dict().items():
            state=self.state.get(named.get(name),{})
            result[name]=state.get('master_param',None)
            if result[name] is None:result[name]=tensor.detach().cpu()
        return result


def validate_against_torch(device='cpu'):
    torch.manual_seed(518)
    a=torch.nn.Parameter(torch.randn(7,5,device=device));b=torch.nn.Parameter(a.detach().clone())
    first=CPUAdam([a]);second=torch.optim.Adam([b],lr=1e-3,foreach=False)
    for _ in range(12):
        grad=torch.randn_like(a);a.grad=grad.clone();b.grad=grad.clone()
        first.step();second.step()
    error=float((a-b).abs().max())
    assert error<1e-6,error
    return error
