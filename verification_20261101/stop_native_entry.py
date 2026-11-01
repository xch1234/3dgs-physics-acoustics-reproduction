"""Stop only this audit's excessively slow optional original evaluator."""
import os,signal,re
from pathlib import Path
from common import ROOT,AUDIT,save,stamp
pid=26
args=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
args=[s.decode() for s in args if s]
expected_source=str(ROOT/'01_PhysGaussian/code/PhysGaussian/gaussian-splatting/metrics.py')
expected_model=str(AUDIT/'outputs/ficus_fresh_30000')
assert expected_source in args and expected_model in args,args
log=(AUDIT/'logs/3dgs-native-metrics.log').read_text(errors='replace')
lines=[line for line in log.splitlines() if re.search(r'\d+/200',line)]
latest=lines[-1];completed=int(re.search(r'(\d+)/200',latest).group(1))
elapsed=float(Path('/proc/uptime').read_text().split()[0])-int(Path(f'/proc/{pid}/stat').read_text().split()[21])/os.sysconf('SC_CLK_TCK')
save('checks/native-entry-stop.json',dict(timestamp=stamp(),pid=pid,verified_command=args,signal='SIGTERM',completed_views=completed,total_views=200,last_progress=latest,process_elapsed_s=elapsed,status='未验证',reason='Original per-image LPIPS wrapper reconstructs the network for each image; measured progress forecasts more than an hour. User permits marking excessive-duration checks unverified. Full 200-view independent streaming evaluation has already completed; do not infer original entry completion.'))
os.kill(pid,signal.SIGTERM)
print('Stopped verified audit metrics process',pid,'after',completed,'of 200 views')
