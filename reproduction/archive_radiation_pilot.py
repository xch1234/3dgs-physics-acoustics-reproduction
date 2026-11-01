"""Preserve the local batch-2 resource pilot before formal released-batch run."""
import json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'03_NeuralSound/outputs/radiation_training').resolve()
destination=(ROOT/'03_NeuralSound/outputs/radiation_pilot_batch2').resolve()
assert source.is_relative_to(ROOT) and destination.is_relative_to(ROOT)
assert source.is_dir() and not destination.exists()
history=json.loads((source/'history.json').read_text())
source.rename(destination)
record=dict(scope='resource and stability pilot, not the final training run',batch_size=2,
    completed_history_epochs=len(history),saved_native_checkpoint_epoch=5,
    checkpoint_source='/opt/3dgs-runtime/checkpoints/neuralsound-radiation-batch2-pilot',
    note='copy native best/last into this folder after archiving; former workspace copies were only epoch 2',
    decision='full batch 40 forward/backward/CPU Adam probe passed at 2.54 GB; formal run restarts from fixed seed for 100 epochs')
(destination/'pilot-status.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(record)
