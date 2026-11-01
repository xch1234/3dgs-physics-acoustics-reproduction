"""Verify final handoff links and index root delivery files without rerunning science."""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def main():
    changed_docs = [ROOT / name for name in (
        'PROGRESS.md', '继续复现执行记录.md', 'reproduction/ACTIVE_HANDOFF.md')]
    links = 0
    for doc in changed_docs:
        for target in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8-sig')):
            if target.startswith(('http:', 'https:', '#', 'mailto:')):
                continue
            target = unquote(target.split('#', 1)[0].strip('<>'))
            assert (doc.parent / target).exists(), (str(doc), target)
            links += 1
    acceptance = json.loads((ROOT / 'reproduction/audit/final-acceptance.json').read_text())
    assert acceptance['extended_check_count'] == 31
    assert acceptance['scene_runs'] == 11 and acceptance['rendered_frames'] == 2275
    for name in ('scope-resume-state.json', 'sh-correction-state.json'):
        assert json.loads((ROOT / 'reproduction' / name).read_text())['status'] == 'completed'
    system = json.loads((ROOT / 'reproduction/audit/final-system-state.json').read_text())
    assert system['own_training_and_simulation_finished']
    files = set(ROOT.glob('*.md')) | set(ROOT.glob('*.ps1')) | set(ROOT.glob('*.py'))
    for pattern in ('*.py', '*.sh', 'scope-final-*.log'):
        files.update((ROOT / 'reproduction').glob(pattern))
    files.update(changed_docs)
    files.update(p for p in (ROOT / 'reproduction/traditional').rglob('*') if p.is_file())
    files.update(ROOT / p for p in (
        'reproduction/extended-artifact-audit.json', 'reproduction/audit/final-acceptance.json',
        'reproduction/audit/final-system-state.json', 'reproduction/audit/scope-visual-review.md',
        'reproduction/scope-resume-state.json', 'reproduction/sh-correction-state.json'))
    counts = {}
    for name in ('01_PhysGaussian', '02_PAT', '03_NeuralSound'):
        path = ROOT / name / 'docs/artifact-manifest.json'
        counts[name] = len(json.loads(path.read_text(encoding='utf-8'))['files'])
        files.add(path)
    assert sum(counts.values()) == 5986
    records = {}
    for path in sorted(files):
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        records[path.relative_to(ROOT).as_posix()] = {
            'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}
    report = dict(
        time=datetime.now().astimezone().isoformat(), passed=True,
        changed_document_links=links, project_manifest_counts=counts, files=records,
        note='Closeout root documents/control scripts/traditional outputs and exact project manifest hashes. '
             'Scientific artifacts were verified separately; this does not claim full-paper accuracy.')
    (ROOT / 'reproduction/audit/closeout-files.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(passed=True, changed_document_links=links,
                         closeout_files=len(records), project_manifest_counts=counts)))


if __name__ == '__main__':
    main()
