"""Read-only provenance follow-up after the canonical download failed."""
from common import ROOT,AUDIT,save
import requests,gdown,json
from bs4 import BeautifulSoup
from importlib.metadata import version
rows=[]
url='https://drive.google.com/file/d/18JxhpWD-4ZmuFKLzKlAw-w5PpzZxXOcG/view'
try:
 r=requests.get(url,timeout=60);soup=BeautifulSoup(r.text,'html.parser')
 rows.append(dict(url=url,status=r.status_code,title=soup.title.get_text() if soup.title else '',visible_text=soup.get_text(' ',strip=True)[:1200]))
except Exception as e:rows.append(dict(url=url,error=repr(e)))
folder='https://drive.google.com/drive/folders/1cK3UDIJqKAAm7zyrxRYVFJ0BRMgrwhh4'
try:
 files=gdown.download_folder(url=folder,quiet=True,skip_download=True)
 rows.append(dict(url=folder,files=[dict(id=f.id,path=f.path) for f in files]))
except Exception as e:rows.append(dict(url=folder,error=repr(e)))
result=dict(gdown_version=version('gdown'),read_only=True,checks=rows)
save('checks/V30-canonical-access.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
