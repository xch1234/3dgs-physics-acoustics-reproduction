"""Independent saved-array checks for the completion-audit extensions."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.linalg import polar
from scipy.special import sph_harm,spherical_jn,spherical_yn

ROOT=Path(__file__).resolve().parents[1]


def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8-sig'))
def relative(a,b):return float(np.linalg.norm(a-b)/np.linalg.norm(b))
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def verify():
    checks=[]
    traditional=read('reproduction/audit/traditional-audit.json')
    assert traditional['passed'] and len(traditional['records'])==5 and traditional['combined_audio_exact']
    checks.append('A1: five saved physical-array cases, independent ODE and six PCM files verified')
    p=ROOT/'01_PhysGaussian'
    m=read('01_PhysGaussian/docs/gaussian-transport-metrics.json')
    assert m['all_checks_passed'] and m['random_cases']==96
    with np.load(p/'outputs/gaussian_transport/reference_arrays.npz') as a:
        F,C,S=a['deformation_gradients'],a['initial_covariances'],a['actual_covariances']
        assert all(np.isfinite(a[k]).all() for k in a.files)
        assert relative(S,F@C@F.transpose(0,2,1))<2e-5
        assert relative(np.linalg.det(S),np.linalg.det(F)**2*np.linalg.det(C))<2e-5
        assert np.linalg.eigvalsh(S).min()>0
        rotations=np.stack([polar(f)[0].T for f in F])
        assert relative(a['actual_inverse_rotations'],rotations)<2e-5
        assert relative(a['original_SH_colors'],a['transformed_SH_colors'])<1e-6
    errors=[v['relative_error'] for v in m['incremental']]
    assert all(1.8<errors[i]/errors[i+1]<2.2 for i in (0,1))
    checks.append('96 original CUDA covariance/polar/SH cases: recomputed invariants; actual g2p first-order convergence retained')
    sh=read('01_PhysGaussian/docs/sh-frame-metrics.json')
    assert sh['adapter_checks_passed'] and not sh['upstream_nonidentity_frame_invariance_passed']
    assert all(row['corrected_color_relative_L2']<1e-12 for row in sh['records'])
    assert min(row['original_color_relative_L2'] for row in sh['records'][1:])>.01
    for name,frames in (('bread',300),('plane',400),('vasedeck',75)):
        folder=p/'outputs'/f'{name}_sh_corrected';d=json.loads((folder/'metrics.json').read_text())
        old=read(f'01_PhysGaussian/outputs/{name}_official_full/metrics.json')
        assert d['all_checks_passed'] and d['sh_frame_correction'] and d['rendered_frames']==frames
        assert d['model_sha256']==old['model_sha256'] and len(d['frames'])==frames
        assert len(list(folder.glob('*.png')))==frames
        with np.load(folder/'final_state.npz') as a:
            assert all(np.isfinite(a[k]).all() for k in a.files)
            assert a['final_positions'].shape==(d['physical_particles'],3)
        np.testing.assert_allclose([r['mass'] for r in d['frames']],d['frames'][0]['mass'],rtol=1e-6)
        paired=d['sh_same_state_comparison'];assert len(paired)==frames
        assert all(np.isfinite(r['relative_image_L2']) and r['relative_image_L2']>=0 for r in paired)
        assert max(r['relative_image_L2'] for r in paired)>0
        assert len(list((folder/'same_state_comparison').glob('*_original.png')))==4
        assert len(list((folder/'same_state_comparison').glob('*_corrected.png')))==4
        raw_pairs=sorted((folder/'same_state_comparison').glob('*_raw.npz'));assert len(raw_pairs)==4
        for path in raw_pairs:
            with np.load(path) as raw:
                original,corrected=raw['original'].astype(float),raw['corrected'].astype(float)
                frame=int(raw['frame'])
            assert original.shape==corrected.shape and original.ndim==3 and original.shape[0]==3
            assert np.isfinite(original).all() and np.isfinite(corrected).all()
            row=paired[frame-1];assert row['frame']==frame
            delta=corrected-original
            np.testing.assert_allclose([relative(corrected,original),np.abs(delta).mean(),np.abs(delta).max()],
                [row['relative_image_L2'],row['mean_absolute_difference'],row['max_absolute_difference']],rtol=2e-5,atol=1e-9)
        checks.append(f'SH corrected {name}: {frames} frames, same original model, paired identical-state rendering and finite physical states')
    an=read('01_PhysGaussian/docs/anisotropy-metrics.json');assert an['all_checks_passed'] and an['iterations']==30000
    assert an['test_views']==200 and an['train_views']==100 and an['threshold']==5 and an['weight']==.01
    function=read('01_PhysGaussian/docs/anisotropy-function-check.json');assert function['passed'] and function['finite_difference_max_absolute_error']<1e-8
    folder=p/'outputs/ficus_anisotropy';model=folder/'point_cloud/iteration_30000/point_cloud.ply'
    assert digest(model)==an['checkpoint_sha256']
    history=json.loads((folder/'anisotropy-history.json').read_text());assert history[-1]['iteration']==30000
    assert all(np.isfinite(r['anisotropy_loss']) and r['anisotropy_loss']>=0 for r in history)
    evaluation=json.loads((folder/'evaluation.json').read_text())
    assert evaluation['test_images']==200 and len(evaluation['per_image'])==200
    render_folder=folder/'test/ours_30000'
    assert len(list((render_folder/'renders').glob('*.png')))==200
    for row in evaluation['per_image']:
        with Image.open(render_folder/'renders'/row['image']) as im:render=np.asarray(im.convert('RGB'),dtype=float)/255
        with Image.open(render_folder/'gt'/row['image']) as im:truth=np.asarray(im.convert('RGB'),dtype=float)/255
        independent_psnr=-10*np.log10(np.mean((render-truth)**2))
        assert abs(independent_psnr-row['PSNR'])<1e-3
    for key in ('SSIM','PSNR','LPIPS'):
        np.testing.assert_allclose(np.mean([r[key] for r in evaluation['per_image']]),evaluation['mean'][key])
    # Gaussian PLY uses binary scalar float properties; read scales without plyfile.
    with model.open('rb') as f:
        header=[]
        while True:
            line=f.readline().decode('ascii').strip();header.append(line)
            if line=='end_header':break
            assert line,'Truncated PLY header'
        assert 'format binary_little_endian 1.0' in header
        properties=[line.split()[2] for line in header if line.startswith('property float ')]
        count=int(next(line.split()[-1] for line in header if line.startswith('element vertex ')))
        ply=np.frombuffer(f.read(),dtype=np.dtype([(key,'<f4') for key in properties]),count=count)
    logs=np.stack([ply[f'scale_{i}'] for i in range(3)],axis=1)
    ply_ratios=np.exp(logs.max(axis=1)-logs.min(axis=1)).astype(float)
    with np.load(folder/'axis_ratio_comparison.npz') as a:
        # exp(float32) can differ by a few ULPs between Linux/Windows NumPy builds.
        np.testing.assert_allclose(a['regularized'],ply_ratios,rtol=2e-6,atol=0)
        for key in ('baseline','regularized'):
            v=a[key];assert np.isfinite(v).all() and (v>=1).all()
            stats=an['axis_ratios'][key]
            assert len(v)==stats['gaussians']
            np.testing.assert_allclose([v.mean(),np.median(v),np.quantile(v,.95),np.mean(v>5)],
                [stats['mean'],stats['median'],stats['percentile95'],stats['fraction_above5']])
    sim=read('01_PhysGaussian/outputs/ficus_anisotropy_full/metrics.json')
    assert sim['all_checks_passed'] and sim['rendered_frames']==125 and sim['model_sha256']==an['checkpoint_sha256']
    assert all(path.isascii() for path in sim['warp_source_modules'].values())
    assert len(list((p/'outputs/ficus_anisotropy_full').glob('*.png')))==125
    with np.load(p/'outputs/ficus_anisotropy_full/final_state.npz') as a:
        assert all(np.isfinite(a[k]).all() for k in a.files)
    checks.append('Anisotropy: loss/gradient check, 30000-step history, independent 200-view PSNR, PLY axis ratios and exact model hash into 125-frame simulation')
    folder=ROOT/'02_PAT/outputs/modalsound_transfer'
    m=read('02_PAT/docs/modalsound-transfer-metrics.json');assert m['all_checks_passed'] and len(m['records'])==9
    with np.load(folder/'reference_arrays.npz') as a:
        points=a['query_points'];r=np.linalg.norm(points,axis=1);theta=np.arccos(points[:,2]/r);az=np.arctan2(points[:,1],points[:,0])
        for row in m['records']:
            tag=f"panels{row['panels']}_hz{int(row['frequency_Hz'])}"
            field=np.loadtxt(folder/f'{tag}_field.txt');data=a[tag]
            assert data.shape==(240,4) and np.isfinite(data).all()
            np.testing.assert_allclose(field[:,3]+1j*field[:,4],data[:,1])
            np.testing.assert_allclose(field[:,5]+1j*field[:,6],data[:,2])
            assert relative(data[:,2],data[:,1])<1e-6
            k=2*np.pi*row['frequency_Hz']/343
            distances=np.linalg.norm(points[:,None,:]-a['sources'][None,:,:],axis=2)
            reference=np.sum(a['strengths'][None,:]*np.exp(1j*k*distances)/(4*np.pi*distances),axis=1)
            np.testing.assert_allclose(data[:,0],reference,rtol=1e-12)
            np.testing.assert_allclose(relative(data[:,1],reference),row['direct_vs_analytic_relative_L2'],rtol=1e-12)
            order=row['expansion_order_count'];blob=(folder/f'{tag}_moments.ma').read_bytes()
            assert blob[:4]==b'MA\x09\x12'
            np.testing.assert_array_equal(np.frombuffer(blob,dtype='<i4',count=3,offset=4),[2,order*order,2])
            values=np.frombuffer(blob,dtype='<f8',offset=16).reshape(2,-1)
            moments=values[0]+1j*values[1];text=np.loadtxt(folder/f'{tag}_moments.txt')
            np.testing.assert_array_equal(moments,text[:,0]+1j*text[:,1])
            result=np.zeros(len(points),complex);i=0
            for n in range(order):
                for mm in range(-n,n+1):
                    result+=moments[i]*(spherical_jn(n,k*r)+1j*spherical_yn(n,k*r))*sph_harm(mm,n,az,theta)*((-1.)**mm if mm>0 else 1.)
                    i+=1
            assert relative(1j*k*result,data[:,2])<1e-10
    checks.append('Nine original ModalSound boundary/multipole cases: exact analytic field recomputation and binary coefficients independently evaluated')
    for task in ('vibration','radiation'):
        folder=ROOT/'03_NeuralSound/outputs'/f'{task}_paper_schedule'
        m=json.loads((folder/'metrics.json').read_text());h=json.loads((folder/'history.json').read_text())
        assert m['training_completed'] and m['epochs']==100 and len(h)==100
        assert all(np.isfinite(r['train_loss']) and np.isfinite(r['validation_loss']) for r in h)
        settings=m['training_settings'];assert settings['initial_learning_rate']==1e-4 and settings['decay_period']==20 and settings['decay_factor']==.5
        assert settings['parameter_updates']==(1600 if task=='vibration' else 600)
        if task=='vibration':
            assert len(m['refinement'])==12
            assert all(r['relative_residual']<1e-6 and r['first_six_elastic_eigenvalue_max_relative_error']<1e-6 for r in m['refinement'])
        else:assert m['batch_size']==16
    audit=read('03_NeuralSound/docs/paper-schedule-checkpoint-audit.json')
    assert audit['passed'] and len(audit['records'])==4
    assert all(r['paper_schedule_verified'] for r in audit['records'] if r['file']=='last.pt')
    arrays_audit=read('03_NeuralSound/docs/paper-schedule-vibration-array-audit.json')
    assert arrays_audit['passed'] and len(arrays_audit['records'])==12
    folder=ROOT/'03_NeuralSound/outputs/radiation_paper_schedule/all_test_predictions'
    exported=json.loads((folder/'export-metrics.json').read_text());assert exported['passed'] and exported['samples']==24
    with np.load(folder/'predictions.npz') as a:
        assert a['predicted_ffat'].shape==(24,64,32) and np.isfinite(a['predicted_ffat']).all()
        errors=np.linalg.norm((a['predicted_ffat']-a['bem_ffat']).reshape(24,-1),axis=1)/np.linalg.norm(a['bem_ffat'].reshape(24,-1),axis=1)
        np.testing.assert_allclose(errors,a['relative_L2'],rtol=1e-5,atol=1e-7)
    checks.append('Paper optimizer control: both 100-epoch schedules and all four states verified; 12 vibration refinements and all 24 raw FFAT errors checked')
    return checks


if __name__=='__main__':print('\n'.join(verify()))
