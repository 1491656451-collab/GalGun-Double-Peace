from hashlib import md5,sha1,sha256
from pathlib import Path
import json
raws=[b'0100517014FE0000',b'0100517014fe0000',bytes.fromhex('0100517014FE0000'),b'GalGun Double Peace',b'GalGun Double Peace\0',b'coalesced_int.bin',b'GG2Game',b'GG2Game/CookedNX/Coalesced_INT.bin',b'..\\GG2Game\\CookedNX\\Coalesced_INT.bin']
items=[]
for r in raws:
 for pref in [b'',b'Coalesced',b'GalGun',b'GG2']:
  for d in [r,pref+r,r+pref]:
   for fn,n in [(lambda x:x,'raw'),(md5,'md5'),(sha1,'sha1'),(sha256,'sha256')]:
    x=fn(d).digest() if n!='raw' else d
    for k in [x,x[::-1]]:
     for size in [16,24,32]:
      if len(k)>=size: items.append({'label':f'{n}:{d!r}:{size}','key':k[:size].hex()})
Path(r'work\aes_candidates_title.json').write_text(json.dumps(items))
print(len(items))
