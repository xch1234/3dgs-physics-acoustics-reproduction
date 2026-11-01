"""Final direct readback of this audit's new trained model and simulation."""
import json,sys
import numpy as np,torch,cv2
from plyfile import PlyData
from PIL import Image,ImageDraw
from common import ROOT,AUDIT,save,digest

def finite_tree(obj):
    if torch.is_tensor(obj):
        assert torch.isfinite(obj).all();return obj.numel()
    if isinstance(obj,dict):return sum(finite_tree(v) for v in obj.values())
    if isinstance(obj,(tuple,list)):return sum(finite_tree(v) for v in obj)
    return 0

def main():
    torch.set_num_threads(2)
    folder=AUDIT/'outputs/ficus_fresh_30000';p=folder/'point_cloud/iteration_30000/point_cloud.ply'
    vertex=PlyData.read(str(p))['vertex'].data
    for name in vertex.dtype.names:assert np.isfinite(vertex[name]).all()
    checkpoint=torch.load(folder/'chkpnt30000.pth',map_location='cpu');assert checkpoint[1]==30000
    elements=finite_tree(checkpoint);del checkpoint
    a=np.column_stack([vertex['scale_'+str(i)] for i in range(3)]).astype(float);assert (np.exp(a)>0).all()
    trained=dict(particles=len(vertex),PLY_SHA256=digest(p),checkpoint_iteration=30000,finite_checkpoint_elements=elements,PLY_fields=len(vertex.dtype.names),mean_axis_ratio=float(np.exp(a.max(1)-a.min(1)).mean()))
    save('checks/fresh-trained-model.json',trained)
    scene=AUDIT/'physics/outputs/ficus_fresh_full';raw=np.load(scene/'final_state.npz')
    for k in raw.files:assert np.isfinite(raw[k]).all(),k
    metrics=json.loads((scene/'metrics.json').read_text());frames=sorted(scene.glob('[0-9][0-9][0-9][0-9].png'))
    assert len(frames)==metrics['rendered_frames']==125
    cap=cv2.VideoCapture(str(scene/'output.mp4'));n=0
    while True:
        ok,frame=cap.read()
        if not ok:break
        n+=1
    cap.release();assert n==125
    displacement=np.linalg.norm(raw['final_positions']-raw['initial_positions'],axis=1)
    determinants=np.linalg.det(raw['final_F'].astype(float));assert determinants.min()>0
    packed=raw['final_covariance'].reshape(-1,6).astype(float);cov=np.zeros((len(packed),3,3))
    for j,(a,b) in enumerate(((0,0),(0,1),(0,2),(1,1),(1,2),(2,2))):cov[:,a,b]=cov[:,b,a]=packed[:,j]
    eigenvalues=np.linalg.eigvalsh(cov);tolerance=64*np.finfo(np.float32).eps*np.maximum(eigenvalues[:,-1],1e-30)
    invalid=int(np.sum(eigenvalues[:,0]<-tolerance));assert invalid==0
    mass=np.array([r['mass'] for r in metrics['frames']]);mass_drift=float(np.max(abs(mass-mass[0]))/mass[0]);assert mass_drift<1e-6
    sheet=Image.new('RGB',(1200,330),'white');draw=ImageDraw.Draw(sheet)
    for j,i in enumerate((0,41,83,124)):
        with Image.open(frames[i]) as im:im=im.convert('RGB');im.thumbnail((300,300));sheet.paste(im,(j*300,25))
        draw.text((j*300+5,5),'fresh simulation frame '+str(i),fill='black')
    sheet.save(scene/'verified_contact_sheet.jpg')
    save('checks/fresh-simulation.json',dict(passed=True,decoded_video_frames=n,PNG_frames=len(frames),particles=len(displacement),max_displacement=float(displacement.max()),minimum_final_det_F=float(determinants.min()),minimum_covariance_eigenvalue=float(eigenvalues.min()),invalid_covariance_count_with_fp32_tolerance=invalid,relative_mass_drift=mass_drift,raw_keys=raw.files,all_raw_arrays_finite=True,scope='New model / complete Ficus config; no external physical ground truth.'))
    print(json.dumps(trained),flush=True)

if __name__=='__main__':main()
