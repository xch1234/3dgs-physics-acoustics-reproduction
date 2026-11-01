"""Read and decode all existing full-scene videos; shell parser checks."""
import sys,json
import cv2,numpy as np
from PIL import Image,ImageDraw
from common import ROOT,AUDIT,save,run,runtime_env

def main():
    rows=[]
    for path in sorted((ROOT/'01_PhysGaussian/outputs').glob('*/output.mp4')):
        expected=json.loads((path.parent/'metrics.json').read_text())['rendered_frames']
        cap=cv2.VideoCapture(str(path));assert cap.isOpened();fps=cap.get(cv2.CAP_PROP_FPS);frames=[];n=0;means=[]
        while True:
            ret,frame=cap.read()
            if not ret:break
            if n in (0,expected//2,expected-1):frames.append(Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)))
            means.append(float(frame.mean()));n+=1
        cap.release();assert n==expected,(path,n,expected);assert len(frames)==3
        row=dict(video=str(path.relative_to(ROOT)),decoded_frames=n,fps=fps,min_frame_mean=min(means),max_frame_mean=max(means),passed=True);rows.append(row)
        sheet=Image.new('RGB',(900,322),'white');draw=ImageDraw.Draw(sheet);draw.text((5,5),path.parent.name,fill='black')
        for i,im in enumerate(frames):im.thumbnail((300,300));sheet.paste(im,(300*i,22))
        out=AUDIT/'media';out.mkdir(exist_ok=True);sheet.save(out/(path.parent.name+'.jpg'));print(row,flush=True)
    save('checks/video-decode.json',rows)
    rows=[]
    for project in ('01_PhysGaussian','02_PAT','03_NeuralSound'):
        for path in sorted((ROOT/project/'code').glob('*.sh')):
            rows.append(run('bash-syntax-'+path.stem,['bash','-n',str(path)],env=runtime_env(),required=False))
    save('checks/bash-syntax.json',rows);assert all(r['exit_code']==0 for r in rows)

if __name__=='__main__':main()
