"""Final decoded-media and saved-array audit, independent of completion strings."""
import json,subprocess
from fractions import Fraction
from common import ROOT,AUDIT,save,digest
import numpy as np
from PIL import Image,ImageDraw,ImageOps
from scipy.io import wavfile
from plyfile import PlyData
ffprobe='/opt/3dgs-runtime/envs/physgaussian/bin/ffprobe'
rows=[];errors=[];figures=AUDIT/'figures';figures.mkdir(exist_ok=True)
def video(path,frames=None,fps=None,audio=None):
 cmd=[ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)]
 r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0 and not r.stderr.strip(),r.stderr
 d=json.loads(r.stdout);v=next(s for s in d['streams'] if s['codec_type']=='video');a=[s for s in d['streams'] if s['codec_type']=='audio']
 n=int(v['nb_read_frames']);rate=float(Fraction(v['r_frame_rate']))
 if frames is not None:assert n==frames,(path,n,frames)
 if fps is not None:assert abs(rate-fps)<1e-5,(path,rate,fps)
 if audio is not None:assert bool(a)==audio,(path,audio,a)
 seconds=float(v.get('duration',n/rate));audio_timing=[]
 for stream in a:
  start=float(stream.get('start_time',0));duration=float(stream['duration'])
  assert int(stream['sample_rate'])==48000
  assert abs(start-float(v.get('start_time',0)))<1/48000
  assert abs(duration-seconds)<=1/rate,(path,'audio/video duration mismatch',duration,seconds)
  audio_timing.append(dict(start_seconds=start,duration_seconds=duration,sample_rate=int(stream['sample_rate']),channels=stream['channels']))
 return dict(path=str(path.relative_to(AUDIT)),frames=n,fps=rate,video_seconds=seconds,audio_streams=len(a),audio_timing=audio_timing,codec=v['codec_name'],sha256=digest(path),command=cmd)
scene_tags=[n+'_rerun' for n in ('ficus','bread','pillow2sofa','plane','vasedeck','wolf')]+[n+'_corrected_rerun' for n in ('bread','plane','vasedeck')]+['ficus_reconstructed_rerun','ficus_anisotropy_rerun','snow_ficus_local','snow_ficus_clean_env']
for tag in scene_tags:
 try:
  folder=AUDIT/'physics/outputs'/tag;m=json.loads((folder/'metrics.json').read_text());cfg=json.loads((folder/'config.json').read_text());frames=sorted(folder.glob('*.png'));assert len(frames)==cfg['frame_num']==m['rendered_frames']
  assert m['all_checks_passed'],(tag,'simulation invariants failed')
  shapes=[]
  for f in frames:
   with Image.open(f) as im:im.load();shapes.append(im.size)
  assert len(set(shapes))==1
  state=dict(np.load(folder/'final_state.npz'))
  for name,value in state.items():
   if value.dtype.kind in 'iufc':assert np.isfinite(value).all(),(tag,name)
  row=video(folder/'output.mp4',len(frames),1/cfg['frame_dt'],False)
  row.update(scene=tag,image_dimensions=list(shapes[0]),arrays_finite=True,particle_count=len(state['final_positions']),minimum_recorded_F_determinant=min(x['min_det_F'] for x in m['frames']),model_sha256=m['model_sha256'])
  row.update(nominal_simulation_seconds=cfg['frame_num']*cfg['frame_dt'],actual_simulation_seconds=m['duration_s'],simulation_minus_video_seconds=m['duration_s']-row['video_seconds'],steps=m['steps'],step_rounding_note='Original simulator uses int(frame_dt/substep_dt); floating-point ratios can truncate one step. Nominal/video and actual simulated times are reported separately; not silently asserted identical.')
  assert row['minimum_recorded_F_determinant']>0,(tag,'recorded deformation inversion',row['minimum_recorded_F_determinant'])
  rows.append(row);print('MEDIA',tag,len(frames),flush=True)
  canvas=Image.new('RGB',(960,345),'white');draw=ImageDraw.Draw(canvas);draw.text((8,7),tag+' / actual rerun frames',fill='black')
  for j,index in enumerate([0,len(frames)//2,len(frames)-1]):
   with Image.open(frames[index]) as im:canvas.paste(ImageOps.contain(im.convert('RGB'),(320,320)),(j*320,25))
  canvas.save(figures/(tag+'_contact.jpg'),quality=92)
  if tag.endswith('_corrected_rerun'):
   assert m['sh_frame_correction'] and len(m['sh_same_state_comparison'])==len(frames)
   raw_files=sorted((folder/'same_state_comparison').glob('*_raw.npz'));assert len(raw_files)==4
   for raw_file in raw_files:
    raw=dict(np.load(raw_file));original=raw['original'];corrected=raw['corrected'];frame=int(raw['frame'])
    measured=float(np.linalg.norm(corrected-original)/np.linalg.norm(original));expected=m['sh_same_state_comparison'][frame-1]['relative_image_L2'];assert abs(measured-expected)<1e-6
    for name,values in [('original',original),('corrected',corrected)]:
     expected_pixels=np.clip(np.moveaxis(values,0,-1)*255+.5,0,255).astype(np.uint8)
     with Image.open(folder/'same_state_comparison'/f'frame_{frame:04d}_{name}.png') as im:actual=np.array(im.convert('RGB'))
     assert np.max(np.abs(actual.astype(int)-expected_pixels.astype(int)))<=1
   canvas=Image.new('RGB',(960,345),'white');draw=ImageDraw.Draw(canvas)
   arrays=[original,corrected,np.clip(np.abs(corrected-original)*20,0,1)]
   for j,(name,a) in enumerate(zip(['Original SH','Corrected SH','Absolute difference x20'],arrays)):
    draw.text((j*320+8,7),tag+' / '+name,fill='black');im=Image.fromarray((np.moveaxis(a,0,-1).clip(0,1)*255).round().astype(np.uint8));canvas.paste(ImageOps.contain(im,(320,320)),(j*320,25))
   canvas.save(figures/(tag+'_same_state.jpg'),quality=95)
 except Exception as e:errors.append(dict(item=tag,error=repr(e)))
for tag in ('unified_beam','unified_neural_box'):
 for name in ('bem_synchronized.mp4','pat_synchronized.mp4' if tag=='unified_beam' else 'neural_synchronized.mp4','slow_motion_silent.mp4'):
  try:rows.append(video(AUDIT/tag/name,120 if name.startswith('slow') else 90,30,not name.startswith('slow')))
  except Exception as e:errors.append(dict(item=tag+'/'+name,error=repr(e)))
 try:
  for directory,count in [('frames',90),('slow_frames',120)]:
   files=sorted((AUDIT/tag/directory).glob('*.png'));assert len(files)==count
   for file in files:
    with Image.open(file) as im:im.load()
   canvas=Image.new('RGB',(1280,470),'white');draw=ImageDraw.Draw(canvas)
   draw.text((8,7),tag+' / '+directory+' / actual generated frames (time/amplification labelled in each frame)',fill='black')
   for j,index in enumerate([0,count//4,count//2,3*count//4]):
    with Image.open(files[index]) as im:canvas.paste(ImageOps.contain(im.convert('RGB'),(640,210)),((j%2)*640,30+(j//2)*220))
   canvas.save(figures/(tag+'_'+directory+'_contact.jpg'),quality=95)
  for file in (AUDIT/tag).glob('*.npz'):
   with np.load(file) as data:
    for key in data.files:
     if data[key].dtype.kind in 'iufc':assert np.isfinite(data[key]).all(),(tag,key)
 except Exception as e:errors.append(dict(item=tag+'/images-and-arrays',error=repr(e)))
wav_rows=[]
for folder,count in [(AUDIT/'pat_phase/outputs/phase_preserving',6),(AUDIT/'pat_extensions/outputs/phase_preserving',8),(AUDIT/'neural_extensions/outputs/neural_audio',6),(AUDIT/'unified_beam',2),(AUDIT/'unified_neural_box',2)]:
 assert len(list(folder.glob('*.wav')))==count,(folder,count)
 for path in folder.glob('*.wav'):
  sr,pcm=wavfile.read(path);assert sr==48000 and pcm.dtype==np.int16 and len(pcm)==144000
  peak=int(np.max(np.abs(pcm.astype(np.int32))));assert 0<peak<32767,(path,'silent or clipped PCM',peak)
  wav_rows.append(dict(path=str(path.relative_to(AUDIT)),sample_rate=sr,samples=len(pcm),peak_PCM=peak,sha256=digest(path)))
model_rows=[]
for name,path in [('fresh_anisotropy',AUDIT/'physics/outputs/ficus_anisotropy/point_cloud/iteration_30000/point_cloud.ply'),('independent_baseline',ROOT/'verification_20261101/outputs/ficus_fresh_30000/point_cloud/iteration_30000/point_cloud.ply')]:
 try:
  v=PlyData.read(str(path))['vertex'].data
  for field in v.dtype.names:assert np.isfinite(v[field]).all(),field
  scales=np.column_stack([v['scale_'+str(i)] for i in range(3)]).astype(float);ratios=np.exp(scales.max(1)-scales.min(1));assert np.isfinite(ratios).all()
  model_rows.append(dict(model=name,sha256=digest(path),gaussians=len(v),mean_axis_ratio=float(ratios.mean()),median_axis_ratio=float(np.median(ratios)),maximum_axis_ratio=float(ratios.max()),fraction_above_5=float((ratios>5).mean())))
 except Exception as e:errors.append(dict(item=name,error=repr(e)))
if len(model_rows)==2:
 save('checks/V28-anisotropy-comparison.json',dict(models=model_rows,mean_ratio_reduced=model_rows[0]['mean_axis_ratio']<model_rows[1]['mean_axis_ratio'],evaluation=json.loads((AUDIT/'evaluations/anisotropy_30000/metrics.json').read_text())['mean'],scope='Repeated local r=5/lambda=.01 control; not original Fig.8 settings.'))
save('checks/final-artifacts.json',dict(passed=not errors,video_and_scene_checks=rows,wav_checks=wav_rows,models=model_rows,errors=errors,scope='All listed media decoded and dimensions/frame counts checked; array/model finiteness. This does not establish paper accuracy or subjective audio quality.'))
print('ARTIFACT ERRORS',json.dumps(errors,indent=2),flush=True)
if errors:raise SystemExit(1)
