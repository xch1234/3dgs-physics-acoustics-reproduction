"""Inventory every extracted checkpoint, without loading huge PLY tensors."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / '01_PhysGaussian'
rows = []
for folder in sorted((ROOT / 'inputs').glob('*-trained')):
    cameras = json.loads((folder / 'cameras.json').read_text())
    checkpoints = []
    for ply in sorted(folder.glob('point_cloud/iteration_*/point_cloud.ply'),
                      key=lambda p: int(p.parent.name.split('_')[-1])):
        with ply.open('rb') as f:
            count = None
            for line in f:
                if line.startswith(b'element vertex '):
                    count = int(line.split()[-1])
                if line.strip() == b'end_header':
                    break
        assert count is not None
        checkpoints.append(dict(iteration=int(ply.parent.name.split('_')[-1]),
                                raw_gaussians=count, ply_bytes=ply.stat().st_size,
                                relative_path=ply.relative_to(ROOT).as_posix()))
    rows.append(dict(model=folder.name, image_width=cameras[0]['width'],
                     image_height=cameras[0]['height'], checkpoints=checkpoints,
                     selected_iteration=max(c['iteration'] for c in checkpoints)))
(ROOT / 'docs/model-resources.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
print(json.dumps(rows, indent=2))
