import hashlib,json,pathlib,tarfile
import os
repo=pathlib.Path(__file__).resolve().parents[1]
base=pathlib.Path(os.environ['MAGE_WORK_DIR']); model=base/'model'
source=json.loads((base/'source-manifest.json').read_text())
files=[]
for f in source['siblings']:
 p=model/f['rfilename']; h=hashlib.sha256()
 with p.open('rb') as r:
  for b in iter(lambda:r.read(8*1024*1024),b''): h.update(b)
 assert p.stat().st_size==f['size'],p
 if f.get('lfs'): assert h.hexdigest()==f['lfs']['sha256'],p
 files.append({'path':f['rfilename'],'size':p.stat().st_size,'sha256':h.hexdigest()})
print('Source files verified',flush=True)
(repo/'parts').mkdir(exist_ok=True)
class Writer:
 def __init__(self): self.f=None; self.n=0; self.size=0; self.parts=[]
 def write(self,data):
  total=len(data)
  while data:
   if self.f is None:
    self.n+=1; self.path=repo/'parts'/f'mage-vl.tar.part{self.n:04d}'; self.f=self.path.open('wb'); self.size=0; self.h=hashlib.sha256()
   block=data[:95*1024*1024-self.size]; self.f.write(block); self.h.update(block); self.size+=len(block); data=data[len(block):]
   if self.size==95*1024*1024: self.finish()
  return total
 def finish(self):
  if self.f:
   self.f.close(); self.parts.append({'path':self.path.relative_to(repo).as_posix(),'size':self.size,'sha256':self.h.hexdigest()}); self.f=None
w=Writer()
with tarfile.open(fileobj=w,mode='w|') as t:
 for f in files: t.add(model/f['path'],arcname='Mage-VL/'+f['path'],recursive=False)
w.finish()
manifest={'source':'https://huggingface.co/microsoft/Mage-VL','revision':source['sha'],'files':files,'parts':w.parts}
(repo/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(repo/'SHA256SUMS').write_text(''.join(f"{p['sha256']}  {p['path']}\n" for p in w.parts))
print('Packaged',len(w.parts),'parts',flush=True)
