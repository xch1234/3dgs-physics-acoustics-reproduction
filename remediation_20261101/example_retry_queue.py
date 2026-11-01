"""Full example retry after all scheduled GPU work and artifact checks."""
import time
from common import AUDIT,run,runtime_env,save
while not (AUDIT/'artifact-review-ready.json').exists():time.sleep(10)
prefix='/opt/3dgs-runtime/envs/neuralsound';rows=[]
for task in ['voxel','solve','compare']:
 row=run('V28-example-retry-'+task,[prefix+'/bin/python','-X','faulthandler','-u',AUDIT/'example_isolated_retry.py',task],env=runtime_env(prefix),required=False);rows.append(row)
 if row['exit_code']!=0:break
save('checks/V28-example-retry.json',dict(passed=len(rows)==3 and all(r['exit_code']==0 for r in rows),original_failed_command='V28-neural-example',original_exit_code=-11,resolution_commands=rows,scope='Complete replay split into PyCUDA voxelization and Torch solve processes, preserving normal teardown. No os._exit, ignored signal, or forced successful exit code. First failed logs/artifacts preserved.'))
save('example-retry-complete.json',dict(failed=[r['name'] for r in rows if r['exit_code']!=0]))
