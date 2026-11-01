"""Decode and inspect final saved artifacts once all producers finish."""
import time,sys
from common import AUDIT,run,runtime_env,save
while not (AUDIT/'clean-pat-complete.json').exists():time.sleep(10)
rows=[]
for name,script in [('final-artifact-validation','validate_deliverables.py'),('V28-fixed-image-comparison','compare_reconstruction_images.py'),('final-source-audit','audit_changes.py')]:
 rows.append(run(name,[sys.executable,'-u',AUDIT/script],env=runtime_env(sys.prefix),required=False))
save('artifact-review-ready.json',dict(failed=[r['name'] for r in rows if r['exit_code']!=0],commands=rows,scope='Generated artifacts require subsequent visual review before final reporting.'))
