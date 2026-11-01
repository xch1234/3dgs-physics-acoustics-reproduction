import subprocess
from common import ROOT,save,digest
p=ROOT/'03_NeuralSound/code/NeuralSound'
names=subprocess.check_output(['git','-C',str(p),'ls-files','-z']).decode().strip('\0').split('\0')
rows=[]
for name in names:
    original=subprocess.check_output(['git','-C',str(p),'show','HEAD:'+name]);actual=(p/name).read_bytes()
    if actual!=original:
        assert actual.replace(b'\r\n',b'\n')==original.replace(b'\r\n',b'\n'),name
        rows.append(dict(file=name,only_CRLF_difference=True,sha256=digest(p/name)))
save('checks/git-lineendings.json',dict(tracked_files=len(names),line_ending_only_differences=rows,semantic_changes=0,process_override='core.autocrlf=true; environment only, no repository/global config writes'))
print('Tracked files',len(names),'CRLF-only',len(rows),'semantic differences',0)
