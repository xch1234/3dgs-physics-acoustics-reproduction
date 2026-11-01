"""Deserialize saved training states on CPU and verify resumable contents."""
import gc
import json
import argparse
from pathlib import Path
import torch

ROOT = Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--paper-schedule',action='store_true');args=p.parse_args()
    torch.set_num_threads(2)
    records = []
    for task, epochs in (('vibration', 200), ('radiation', 100)):
        if args.paper_schedule:epochs=100
        folder = ROOT/'03_NeuralSound/outputs'/(f'{task}_paper_schedule' if args.paper_schedule else f'{task}_training')
        history = json.loads((folder/'history.json').read_text())
        for name in ('best.pt', 'last.pt'):
            ck = torch.load(folder/name, map_location='cpu')
            state = ck['model'] if 'model' in ck else ck
            assert all(torch.isfinite(t).all().item() for t in state.values())
            row = dict(task=task, file=name, model_tensors=len(state),
                       model_elements=sum(t.numel() for t in state.values()), finite=True)
            if name == 'last.pt':
                assert ck['epoch']+1 == epochs
                assert ck['history'] == history
                assert all(k in ck for k in ('optimizer','scheduler','rng_numpy','rng_torch','rng_cuda'))
                tensors = [v for s in ck['optimizer']['state'].values() for v in s.values() if torch.is_tensor(v)]
                assert tensors and all(torch.isfinite(t).all().item() for t in tensors)
                row.update(completed_epochs=ck['epoch']+1, optimizer_tensors=len(tensors),
                           scheduler_and_random_state_present=True)
                if args.paper_schedule:
                    assert ck['scheduler']['step_size']==20 and ck['scheduler']['gamma']==.5
                    assert ck['scheduler']['last_epoch']==100
                    assert all(abs(g['lr']-1e-4*.5**5)<1e-12 for g in ck['optimizer']['param_groups'])
                    row['paper_schedule_verified']=True
                del tensors
            elif task == 'radiation':
                selected = min(history, key=lambda r:r['validation_loss'])['epoch']
                assert ck['epoch']+1 == selected
                row['selected_epoch'] = selected
            records.append(row)
            print(row, flush=True)
            del ck, state
            gc.collect()
    data = dict(passed=True, records=records,
                scope='CPU deserialization, all model/optimizer tensors finite, epochs/history/RNG consistency; no training rerun')
    name='paper-schedule-checkpoint-audit.json' if args.paper_schedule else 'checkpoint-audit.json'
    (ROOT/'03_NeuralSound/docs'/name).write_text(json.dumps(data,indent=2))


if __name__ == '__main__':
    main()
