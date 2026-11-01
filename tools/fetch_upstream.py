"""Fetch pinned upstream checkouts, without resetting or altering existing directories."""
from pathlib import Path
import argparse,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--list',action='store_true');a=ap.parse_args()
 items=json.loads((ROOT/'sharing/upstream.json').read_text(encoding='utf8'))
 for r in items:
  if a.list:print(r['path'],r['url'],r['commit']);continue
  p=ROOT/r['path']
  if p.exists():
   result=subprocess.run(['git','-C',str(p),'rev-parse','HEAD'],text=True,capture_output=True)
   if result.returncode or result.stdout.strip()!=r['commit']:raise RuntimeError(f'Existing directory differs: {p}; nothing overwritten')
  else:
   p.parent.mkdir(parents=True,exist_ok=True)
   subprocess.run(['git','clone','--no-checkout',r['url'],str(p)],check=True)
   subprocess.run(['git','-C',str(p),'checkout','--detach',r['commit']],check=True)
  subprocess.run(['git','-C',str(p),'-c','url.https://github.com/.insteadOf=git@github.com:','submodule','update','--init','--recursive'],check=True)
  print('Ready',r['path'])
if __name__=='__main__':main()
