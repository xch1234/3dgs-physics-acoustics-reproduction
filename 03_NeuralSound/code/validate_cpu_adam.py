"""Independent torch Adam comparison, including CUDA transfers and resume."""
import json,io,time
from pathlib import Path
import torch
from cpu_adam import CPUAdam


def check(device):
    torch.manual_seed(518)
    model=torch.nn.Sequential(torch.nn.Linear(64,128),torch.nn.Linear(128,4)).to(device)
    reference=torch.nn.Sequential(torch.nn.Linear(64,128),torch.nn.Linear(128,4)).to(device)
    reference.load_state_dict(model.state_dict())
    first=CPUAdam(model.parameters());second=torch.optim.Adam(reference.parameters(),lr=1e-3,foreach=False)
    errors=[]
    for step in range(18):
        for a,b in zip(model.parameters(),reference.parameters()):
            grad=torch.randn_like(a);a.grad=grad;b.grad=grad.clone()
        first.step();second.step()
        errors.append(max(float((a-b).abs().max()) for a,b in zip(model.parameters(),reference.parameters())))
        if step==8:
            checkpoint=io.BytesIO()
            torch.save(dict(model=first.model_state_dict(model),optimizer=first.state_dict()),checkpoint)
            checkpoint.seek(0);saved=torch.load(checkpoint,map_location='cpu')
            resumed=torch.nn.Sequential(torch.nn.Linear(64,128),torch.nn.Linear(128,4)).to(device)
            resumed.load_state_dict(saved['model']);optimizer=CPUAdam(resumed.parameters())
            optimizer.load_state_dict(saved['optimizer']);model,first=resumed,optimizer
    assert max(errors)<1e-6,errors
    return dict(device=device,steps=18,resume_after_step=9,max_parameter_difference=max(errors))


if __name__=='__main__':
    torch.set_num_threads(2)
    rows=[check('cpu'),check('cuda:0')]
    path=Path(__file__).resolve().parents[1]/'docs/cpu-adam-master-reference.json'
    path.write_text(json.dumps(rows,indent=2));print(rows,flush=True)
