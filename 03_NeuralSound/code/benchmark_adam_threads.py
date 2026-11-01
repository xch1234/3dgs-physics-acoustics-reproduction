"""Measure CPU Adam arithmetic thread counts under the actual machine load."""
import json,time
from pathlib import Path
import numpy as np
import torch
torch.manual_seed(42)
gradient=torch.randn(8_000_000);rows=[]
for threads in (2,8,4,12):
    torch.set_num_threads(threads)
    m=torch.zeros_like(gradient);v=torch.zeros_like(gradient);p=torch.zeros_like(gradient)
    durations=[]
    for trial in range(10):
        start=time.perf_counter()
        m.mul_(.9).add_(gradient,alpha=.1);v.mul_(.999).addcmul_(gradient,gradient,value=.001)
        denominator=v.sqrt().div_(.1).add_(1e-8)
        p.addcdiv_(m,denominator,value=-.001)
        if trial>=2:durations.append(time.perf_counter()-start)
    rows.append(dict(threads=threads,median_seconds=float(np.median(durations)),raw_seconds=durations))
report=dict(scope='CPU arithmetic only, 8 million floats; measured while radiation training is active',results=rows)
path=Path(__file__).resolve().parents[1]/'docs/cpu-adam-thread-benchmark.json'
path.write_text(json.dumps(report,indent=2));print(report,flush=True)
