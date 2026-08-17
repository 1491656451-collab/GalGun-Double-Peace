from hashlib import md5, sha1, sha256
from pathlib import Path
import json
name=b'coalesced_int.bin'
h=bytes.fromhex('0bad299aa9725f57ea7351f93ff874a76b89dc11')
parts={'name':name,'name_upper':name.upper(),'hash':h,'hashhex':h.hex().encode(),'empty':b''}
items=[]
def add(label,b):
 for n in (16,24,32):
  if len(b)==n: items.append({'label':label,'key':b.hex()})
for l,b in parts.items(): add(l,b)
for l,b in list(parts.items()):
 for alg,fn in [('md5',md5),('sha1',sha1),('sha256',sha256)]:
  d=fn(b).digest(); add(f'{alg}({l})',d)
for a,aa in parts.items():
 for b,bb in parts.items():
  for sep,ss in [('+',b''),(':',b':')]:
   d=aa+ss+bb
   for alg,fn in [('md5',md5),('sha1',sha1),('sha256',sha256)]: add(f'{alg}({a}{sep}{b})',fn(d).digest())
json.dump(items,open(r'work\aes_candidates.json','w'),indent=2)
print(len(items))
