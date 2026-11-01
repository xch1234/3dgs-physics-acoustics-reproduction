"""Record final lightweight metadata checks; do not rebuild or rerun GPU work."""
import sys,json
from common import AUDIT,run,save,digest
run('V03-final-export-audit',[sys.executable,'-u',AUDIT/'finalize_windows_exports.py'])
run('V29-final-resource-inventory',[sys.executable,'-u',AUDIT/'resource_inventory.py'])
records=[]
for script,log,result in [('check_remote.py','logs/V30-remote.log','checks/V30-remote.json'),('plot_cpu_evidence.py',None,'checks/CPU-figures.json'),('plot_snow.py',None,'checks/snow-figures.json')]:
 records.append(dict(producer=script,producer_sha256=digest(AUDIT/script),replay_command=['python',str(AUDIT/script)],existing_log=log,evidence=result,evidence_sha256=digest(AUDIT/result),recording_note='Original full shell argument list and start/end times were not separately retained. This is a replay entry point, not an invented historical command record. Existing numerical/log artifacts remain available.'))
save('checks/supplemental-evidence-index.json',records)
print('Final metadata checked; missing historical timings explicitly labelled.')
