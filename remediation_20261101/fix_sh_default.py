from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];A=R/'remediation_20261101'
p=R/'01_PhysGaussian/code/run_official_linux.py';shutil.copy2(p,A/'backups/run_official_linux.py');s=p.read_text(encoding='utf8');old="parser.add_argument('--correct-sh-frame',action='store_true',help='Opt-in external basis conversion for SH inverse rotations; preserve original runs separately')"
new="""frame=parser.add_mutually_exclusive_group()
    frame.add_argument('--correct-sh-frame',dest='correct_sh_frame',action='store_true',help='Use the world-basis SH rotation correction (default)')
    frame.add_argument('--legacy-sh-frame',dest='correct_sh_frame',action='store_false',help='Explicit historical upstream behavior, including its known nonidentity-basis error')
    parser.set_defaults(correct_sh_frame=True)"""
assert old in s;s=s.replace(old,new);s=s.replace("Opt-in conjugation of MPM inverse rotation", "Conjugation of MPM inverse rotation")
# Default to a separate tag to avoid replacing the historically uncorrected output.
s=s.replace("default='ficus_official_full'","default='ficus_frame_corrected_full'")
p.write_text(s,encoding='utf8')
p=R/'01_PhysGaussian/code/run_scene_suite.py';shutil.copy2(p,A/'backups/run_scene_suite.py');s=p.read_text(encoding='utf8').replace("tag=f'{scene}_official_full'", "tag=f'{scene}_frame_corrected_full'");p.write_text(s,encoding='utf8')
# Queue file is still waiting in its interpreter, so changing its text will NOT
# alter the already-running queue. The original-scene subset will now use the
# corrected wrapper default, and each output explicitly records that flag.
(A/'checks/V17-default-change.json').write_text('''{"change":"local scene runner defaults to corrected SH basis; --legacy-sh-frame preserves deliberate comparison mode","upstream_source_modified":false,"new_default_output_suffix":"frame_corrected_full","actual_tests":"pending GPU queue"}''',encoding='utf8')
print('Local SH runner now defaults to corrected path with separate output tags')
