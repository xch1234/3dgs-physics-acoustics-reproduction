import gc,json,sys
from common import ROOT,AUDIT,save,digest
import torch
def main():
    torch.set_num_threads(2);rows=[]
    for tag in ('vibration_training','vibration_paper_schedule','radiation_training','radiation_paper_schedule'):
        folder=ROOT/'03_NeuralSound/outputs'/tag;history=json.loads((folder/'history.json').read_text())
        for name in ('best.pt','last.pt'):
            obj=torch.load(folder/name,map_location='cpu');state=obj.get('model',obj)
            tensors=list(state.values());assert all(torch.is_tensor(t) and torch.isfinite(t).all() for t in tensors)
            row=dict(run=tag,file=name,model_elements=sum(t.numel() for t in tensors),model_tensors=len(tensors))
            if name=='last.pt':
                assert obj['epoch']+1==len(history) and obj['history']==history
                states=[v for s in obj['optimizer']['state'].values() for v in s.values() if torch.is_tensor(v)]
                assert states and all(torch.isfinite(v).all() for v in states)
                assert all(k in obj for k in ('rng_torch','rng_cuda','rng_numpy','scheduler'))
                row.update(saved_epochs=obj['epoch']+1,optimizer_tensors=len(states),scheduler=obj['scheduler'],random_state_present=True)
                del states
            elif tag.startswith('radiation'):
                selected=min(history,key=lambda r:r['validation_loss'])['epoch'];assert obj['epoch']+1==selected;row['selected_epoch']=selected
            row['readback_passed']=True;rows.append(row);save('checks/checkpoints.json',rows);print(row,flush=True)
            del obj,state,tensors;gc.collect()
    assert len(rows)==8
if __name__=='__main__':main()
