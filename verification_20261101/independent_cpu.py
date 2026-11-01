"""New read-only checks; never trusts previous passed/status fields."""
import os
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
import json,wave,sys,ast,subprocess
import numpy as np
from scipy.linalg import eigh
from scipy.sparse import load_npz
from PIL import Image
from common import ROOT,AUDIT,run,runtime_env,save,digest

def traditional():
    folder=ROOT/'reproduction/traditional/outputs';m=json.loads((folder/'metrics.json').read_text());p=m['parameters'];n=p['masses'];records=[]
    for name,c in m['cases'].items():
        a=np.load(folder/f'{name}_raw.npz');M=np.eye(n)*p['mass_kg']*c['mass_scale'];D=np.eye(n)-np.eye(n,k=-1)
        K=D.T@D*p['spring_stiffness_N_per_m']*c['stiffness_scale']
        np.testing.assert_allclose(a['M_kg'],M);np.testing.assert_allclose(a['K_N_per_m'],K)
        w=2*np.sqrt(p['spring_stiffness_N_per_m']*c['stiffness_scale']/(p['mass_kg']*c['mass_scale']))*np.sin((2*np.arange(1,n+1)-1)*np.pi/(4*n+2))
        np.testing.assert_allclose(a['frequencies_Hz'],w/(2*np.pi),rtol=1e-11)
        U=a['modes_mass_normalized'];E=a['eigenvalues'];KU=K@U;MU=M@U
        rr=np.linalg.norm(KU-MU*E,axis=0)/(np.linalg.norm(KU,axis=0)+np.linalg.norm(MU*E,axis=0));assert rr.max()<1e-10
        np.testing.assert_allclose(U.T@M@U,np.eye(n),atol=1e-12)
        hit=np.zeros(n);hit[c['hit_node_1based']-1]=p['impulse_N_s'];v=U.T@hit
        d=c['damping_scale']*(p['rayleigh_alpha_per_s']+p['rayleigh_beta_s']*w*w)/2
        keep=(w/(2*np.pi)>=p['minimum_frequency_Hz'])&(w/(2*np.pi)<min(p['maximum_frequency_Hz'],.45*p['sample_rate_Hz']))
        np.testing.assert_array_equal(a['retained'],keep);np.testing.assert_allclose(a['modal_initial_velocity'],v,atol=1e-14);np.testing.assert_allclose(a['decay_rate_per_s'],d)
        t=a['time_s'];wd=np.sqrt(w[keep]**2-d[keep]**2)
        vel=v[keep,None]*np.exp(-d[keep,None]*t)*(np.cos(wd[:,None]*t)-d[keep,None]/wd[:,None]*np.sin(wd[:,None]*t))
        # Measurement node is explicitly specified by the experiment parameters.
        probe=p.get('measurement_node_1based',n)-1
        expected=U[probe,keep]@vel
        error=float(np.linalg.norm(expected-a['velocity_m_per_s'])/np.linalg.norm(a['velocity_m_per_s']));assert error<1e-9
        fade=np.ones(len(t));fade[-round(p['playback_tail_fade_s']*p['sample_rate_Hz']):]=np.linspace(1,0,round(p['playback_tail_fade_s']*p['sample_rate_Hz']))
        pcm=np.rint(a['velocity_m_per_s']*m['playback_common_gain_per_m_per_s']*fade*32767).astype('<i2')
        with wave.open(str(folder/f'{name}.wav')) as f:actual=np.frombuffer(f.readframes(f.getnframes()),'<i2');assert f.getframerate()==p['sample_rate_Hz']
        np.testing.assert_array_equal(actual,pcm);assert 0<abs(pcm.astype(int)).max()<32767
        records.append(dict(case=name,analytic_frequency_error=float(np.max(np.abs(a['frequencies_Hz']-w/(2*np.pi)))),waveform_relative_L2=error,eigen_residual=float(rr.max()),exact_PCM=True))
    save('checks/traditional.json',dict(passed=True,records=records,method='Closed-form fixed/free chain frequencies, newly assembled incidence-matrix K, analytic damped velocity recomputed over full waveform'))

def data():
    source=ROOT/'01_PhysGaussian/inputs/nerf_synthetic_ficus';provenance=json.loads((ROOT/'01_PhysGaussian/docs/ficus-dataset-provenance.json').read_text());rows=[]
    for r in provenance['files']:
        f=source/r['file'].replace('\\','/');assert digest(f)==r['sha256'],f
    for split,expected in [('train',100),('test',200),('val',100)]:
        frames=json.loads((source/f'transforms_{split}.json').read_text())['frames'];assert len(frames)==expected
        hashes=[];cameras=[]
        for f in frames:
            p=source/(f['file_path']+'.png')
            with Image.open(p) as im:im.load();assert im.size==(800,800) and im.mode=='RGBA'
            transform=np.array(f['transform_matrix']);assert transform.shape==(4,4) and np.isfinite(transform).all();hashes.append(digest(p));cameras.append(transform)
        rows.append(dict(split=split,count=len(frames),hashes=hashes,cameras=np.array(cameras).tolist()))
    overlap=set(rows[0]['hashes'])&set(rows[1]['hashes']);assert not overlap
    neural=ROOT/'03_NeuralSound/inputs/procedural_bempp';splits={k:(neural/f'{k}.txt').read_text().splitlines() for k in ('train','val','test')};names=sum(splits.values(),[])
    assert len(names)==len(set(names))==24 and [len(splits[k]) for k in ('train','val','test')]==[16,4,4]
    voxels=[]
    for name in names:
        with np.load(neural/name) as a:
            assert a['feats_out_far'].shape==(6,64,32);assert np.isfinite(a['feats_out_far']).all();assert (a['feats_out_far']>=0).all();voxels.append(__import__('hashlib').sha256(a['voxel'].tobytes()).hexdigest())
    assert len(set(voxels))==24
    save('checks/data.json',dict(passed=True,ficus_files_hashed=len(provenance['files']),ficus=rows,train_test_identical_file_count=len(overlap),neural_split=splits,distinct_voxels=len(set(voxels)),limitation='Local bytes matched recorded provenance; remote mirror authenticity and full ABC dataset are not verified by this check.'))

def saved_physics():
    rows=[]
    for p in sorted((ROOT/'01_PhysGaussian/outputs').glob('*/final_state.npz')):
        with np.load(p) as a:
            for k in a.files:assert np.isfinite(a[k]).all(),(p,k)
            displacement=np.linalg.norm(a['final_positions']-a['initial_positions'],axis=1)
            m=json.loads((p.parent/'metrics.json').read_text())
            images=list(p.parent.glob('*.png'));assert len(images)==len(m['frames'])==m['rendered_frames']
            for image in images:
                with Image.open(image) as im:im.verify()
            mass=np.array([x['mass'] for x in m['frames']]);assert np.max(abs(mass/mass[0]-1))<1e-6
            rows.append(dict(scene=p.parent.name,frames=len(images),particles=len(displacement),max_final_displacement=float(displacement.max()),min_final_det=float(np.linalg.det(a['final_F']).min())))
    assert len(rows)==11
    save('checks/saved-physics.json',dict(passed=True,records=rows,note='Re-read all final arrays and PNG headers, independently recomputed finite states and determinants; historical trajectories and real-world accuracy are not proven.'))

def saved_acoustics():
    rows=[]
    for tag in ('radiation_training','radiation_paper_schedule'):
        with np.load(ROOT/'03_NeuralSound/outputs'/tag/'all_test_predictions/predictions.npz') as a:
            truth=a['bem_ffat'];pred=a['predicted_ffat'];assert truth.shape==pred.shape==(24,64,32)
            error=np.sqrt(np.sum((pred.astype(float)-truth)**2,axis=(1,2))/np.sum(truth.astype(float)**2,axis=(1,2)))
            np.testing.assert_allclose(error,a['relative_L2'],rtol=1e-5)
            rows.append(dict(run=tag,mean_relative_L2=float(error.mean()),median_relative_L2=float(np.median(error)),maximum_relative_L2=float(error.max()),negative_prediction_fraction=float((pred<0).mean()),sample_errors=error.tolist()))
    save('checks/saved-radiation-errors.json',dict(passed=True,records=rows,note='Error-record consistency passed; this is not a learned accuracy success.'))
    folder=ROOT/'03_NeuralSound/outputs/official_example';K=load_npz(folder/'stiffness.npz');M=load_npz(folder/'mass.npz');a=np.load(folder/'reference_modes.npz');U=a['modes'];E=a['eigenvalues']
    KU=K@U;MU=M@U;res=np.linalg.norm(KU-MU*E,axis=0)/(np.linalg.norm(KU,axis=0)+np.linalg.norm(MU*E,axis=0));assert res.max()<1e-6
    save('checks/saved-official-fem.json',dict(passed=True,max_residual=float(res.max()),modes=U.shape[1]))

def sources():
    rows=[]
    for folder,repo in [('01_PhysGaussian','PhysGaussian'),('02_PAT','ModalSound'),('03_NeuralSound','NeuralSound')]:
        path=ROOT/folder/'code'/repo
        commit=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
        status=subprocess.check_output(['git','-C',str(path),'status','--porcelain','--untracked-files=no'],text=True)
        rows.append(dict(repo=repo,commit=commit,tracked_status=status,clean=not bool(status.strip())))
    scripts=[]
    for part in ('01_PhysGaussian/code','02_PAT/code','03_NeuralSound/code','reproduction'):
        for p in (ROOT/part).glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'));scripts.append(p.relative_to(ROOT).as_posix())
    save('checks/source.json',dict(repositories=rows,local_python_scripts_parsed=scripts))

def main():
    results=[]
    for name,fn in [('sources',sources),('data',data),('traditional',traditional),('saved_physics',saved_physics),('saved_acoustics',saved_acoustics)]:
        try:fn();results.append(dict(check=name,passed=True));print('PASS',name,flush=True)
        except Exception as exc:
            import traceback;traceback.print_exc();results.append(dict(check=name,passed=False,error=repr(exc)))
    save('checks/cpu-suite.json',results)
    if not all(r['passed'] for r in results):raise SystemExit(1)
if __name__=='__main__':main()
