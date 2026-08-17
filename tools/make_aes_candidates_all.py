from pathlib import Path
import json,hashlib
# hashes parsed from local table
rows=[]
for line in Path(r'work\parse_resource_table.py').read_text(): pass
raw=Path(r'work\parse_resource_table.py')
# manually use a small parser
b=Path(r'work\nso\main.uncompressed').read_bytes(); p=0x19c23c5; end=0x19c25b0
while p<end:
 q=b.find(b'\0',p)
 if q<0 or q+21>end: break
 name=b[p:q]
 if not all(32<=x<127 for x in name): break
 p=q+1; h=b[p:p+20];p+=20
 rows.append((name,h))
items=[]
def add(label,d):
 for alg,fn in [('raw',lambda x:x),('md5',hashlib.md5),('sha1',hashlib.sha1),('sha256',hashlib.sha256)]:
  x=fn(d).digest() if alg!='raw' else d
  for n in [16,24,32]:
   if len(x)>=n: items.append({'label':f'{label}:{alg}:{n}','key':x[:n].hex()})
for name,h in rows:
 add(name.decode(),h); add(name.decode()+'+name',h+name); add('name+hash:'+name.decode(),name+h); add('filename',name); add('filename_upper',name.upper())
Path(r'work\aes_candidates_all.json').write_text(json.dumps(items,indent=2))
print(len(items))
