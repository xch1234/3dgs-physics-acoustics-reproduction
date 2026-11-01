"""Audit saved reproduction artifacts without rerunning scientific experiments.

Run with .conda/acoustics/python.exe. Writes dated document/manifests; does not
turn module-level successes into full-paper reproduction claims.
"""
import ast
import hashlib
import json
import re
import subprocess
import wave
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
PROJECTS = ('01_PhysGaussian', '02_PAT', '03_NeuralSound')
REPOS = ('PhysGaussian', 'ModalSound', 'NeuralSound')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def main():
    stamp = datetime.now().astimezone().isoformat(timespec='seconds')
    checks = []
    for folder in ('acoustics', 'physgaussian'):
        env_python = ROOT / '.conda' / folder / 'python.exe'
        result = subprocess.run([str(env_python), '-m', 'pip', 'check'], text=True,
                                capture_output=True, check=True)
        checks.append(f'PASS：Conda {folder} pip check：{result.stdout.strip()}')
    ps_entries = [ROOT / 'run_all.ps1', ROOT / 'run_full.ps1']
    for folder in PROJECTS:
        ps_entries.extend((ROOT / folder).glob('*.ps1'))
    for script in ps_entries:
        quoted = str(script).replace("'", "''")
        command = "$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile('" + quoted + "',[ref]$t,[ref]$e)|Out-Null;if($e){throw $e}"
        subprocess.run(['powershell', '-NoProfile', '-Command', command], capture_output=True, check=True)
    checks.append(f'PASS：{len(ps_entries)} 个 PowerShell 入口语法检查。汇总入口未重复执行全部 GPU 实验。')
    shell_entries=list((ROOT/'reproduction').glob('*.sh'))
    for folder in PROJECTS:
        shell_entries.extend((ROOT/folder/'code').glob('*.sh'))
    for script in shell_entries:
        linux_path='/mnt/'+script.drive[0].lower()+script.as_posix()[2:]
        subprocess.run(['wsl','-d','Ubuntu1','--','bash','-n',linux_path],capture_output=True,check=True)
    checks.append(f'PASS：{len(shell_entries)} 个本地 Linux shell 入口语法检查。')
    metric_paths = (
        '01_PhysGaussian/outputs/mpm_gaussians/metrics.json',
        '01_PhysGaussian/outputs/ficus_short/metrics.json',
        '02_PAT/outputs/pat_pipeline/metrics.json',
        '03_NeuralSound/outputs/official_fem/metrics.json',
    )
    for rel in metric_paths:
        metrics = json.loads((ROOT / rel).read_text(encoding='utf-8-sig'))
        assert metrics['all_checks_passed'] is True, rel
        checks.append(f'PASS：{rel} 中实验检查全部通过。')
    pairs = (
        (metric_paths[0], '01_PhysGaussian/docs/mpm-metrics.json'),
        (metric_paths[1], '01_PhysGaussian/docs/ficus-metrics.json'),
        (metric_paths[2], '02_PAT/docs/metrics.json'),
        (metric_paths[3], '03_NeuralSound/docs/metrics.json'),
    )
    for source, snapshot in pairs:
        assert digest(ROOT / source) == digest(ROOT / snapshot), snapshot
    provenance = json.loads((ROOT / '02_PAT/docs/input-provenance.json').read_text(encoding='utf-8'))
    assert digest(ROOT / '02_PAT/inputs/official_fem_result.npz') == provenance['sha256']
    checks.append('PASS：文档指标与输出一致，PAT 固定输入匹配 2026-11-01 官方 FEM 来源记录。')

    for folder in PROJECTS:
        for script in (ROOT / folder / 'code').glob('*.py'):
            ast.parse(script.read_text(encoding='utf-8-sig'), filename=str(script))
    for script in (ROOT / 'reproduction').glob('*.py'):
        ast.parse(script.read_text(encoding='utf-8-sig'), filename=str(script))
    ast.parse(Path(__file__).read_text(encoding='utf-8'))
    checks.append('PASS：本地 Python 入口及适配器语法检查。')

    for filename, expected in (
        ('mpm_gaussians/soft.gif', 81), ('mpm_gaussians/stiff.gif', 81),
        ('ficus_short/ficus_diagnostic.gif', 13),
    ):
        with Image.open(ROOT / '01_PhysGaussian/outputs' / filename) as im:
            assert im.n_frames == expected, (filename, im.n_frames)
            for index in range(im.n_frames):
                im.seek(index)
                im.load()
        checks.append(f'PASS：{filename} 可解码，共 {expected} 帧。')

    wavs = sorted((ROOT / '02_PAT/outputs/pat_pipeline').glob('*.wav'))
    assert len(wavs) == 6
    for path in wavs:
        with wave.open(str(path), 'rb') as f:
            assert (f.getnchannels(), f.getsampwidth(), f.getframerate(), f.getnframes()) == (1, 2, 48000, 144000)
            samples = np.frombuffer(f.readframes(f.getnframes()), dtype='<i2').astype(np.int32)
        assert 0 < np.abs(samples).max() < 32767, path
    checks.append('PASS：6 段 PAT/BEM WAV 均为单声道 PCM16、48 kHz、3 s，非静音且无满幅削波。未进行主观听感评价。')

    for folder, repo_name in zip(PROJECTS, REPOS):
        base = ROOT / folder
        repo = base / 'code' / repo_name
        tracked = git(repo, 'status', '--porcelain', '--untracked-files=no')
        assert not tracked, (folder, tracked)
        files = [*base.glob('*.ps1'), *base.glob('README.md')]
        for pattern in ('*.py','*.sh','*.cpp'):
            files.extend(base.joinpath('code').glob(pattern))
        dependency_dir=base/'code/dependencies'
        if dependency_dir.exists():files.extend(p for p in dependency_dir.rglob('*') if p.is_file())
        for part in ('inputs', 'outputs', 'paper', 'docs', 'logs'):
            files += [p for p in (base / part).rglob('*') if p.is_file() and p.name != 'artifact-manifest.json']
        manifest = dict(recorded_at=stamp, upstream_commit=git(repo, 'rev-parse', 'HEAD'),
                        upstream_tracked_files_unmodified=True, files={
            str(p.relative_to(base)).replace('\\', '/'): dict(bytes=p.stat().st_size, sha256=digest(p))
            for p in sorted(set(files))
        })
        if folder == '01_PhysGaussian':
            manifest['submodules'] = git(repo, 'submodule', 'status', '--recursive').splitlines()
        (base / 'docs/artifact-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        checks.append(f'PASS：{repo_name} 跟踪文件未修改，已生成 {len(manifest["files"])} 项文件哈希记录。')

    # This report is created before checking links so it can be a link target.
    report = ROOT / '交付验证记录.md'
    report.write_text('# 交付文件验证记录\n\n生成时间：' + stamp + '\n\n' +
                      '\n'.join('- ' + c for c in checks) + '\n', encoding='utf-8')
    docs = [ROOT / name for name in ('README.md', '复现总报告.md', 'REPRODUCTION_PLAN.md',
            'STATUS.md', 'PROGRESS.md', '最终验收报告.md', '复跑与环境说明.md', '扩展产物验证记录.md',
            'reproduction/audit/scope-visual-review.md', 'reproduction/traditional/ACCEPTANCE.md')]+[report]
    for folder in PROJECTS:
        docs += [ROOT / folder / 'README.md', *(ROOT / folder / 'docs').glob('*.md')]
    links = 0
    for doc in docs:
        for target in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8-sig')):
            if target.startswith(('http:', 'https:', '#', 'mailto:')):
                continue
            target = unquote(target.split('#', 1)[0].strip('<>'))
            assert (doc.parent / target).exists(), (doc, target)
            links += 1
    with report.open('a', encoding='utf-8') as f:
        f.write(f'- PASS：当前交付说明中 {links} 个本地 Markdown 链接目标存在。\n\n')
        f.write('本检查验证已保存结果的完整性与来源，不重新运行物理/声学求解，不证明完整论文复现。原始数值验收标准与局限见各 docs/REPRODUCTION.md。\n\n')
        f.write('重跑：`.\\.conda\\acoustics\\python.exe .\\verify_artifacts.py`。每次会刷新文件哈希与此记录；哈希用于标记当前快照，不包含 manifest 自身，也不代替 Git 版本控制。\n')
    print('\n'.join(checks))
    print(f'PASS: {links} local documentation links; all saved-artifact checks passed.')


if __name__ == '__main__':
    main()
