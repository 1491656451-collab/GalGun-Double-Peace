from pathlib import Path
import struct
p=Path(r'D:\GALGUNVV\romfs\GG2Game\CookedNX\Common_Prologue_map.xxx');b=p.read_bytes();print(len(b),[hex(x) for x in struct.unpack_from('<6I',b,0)]);magic,ver,ct,ut,fc,fu=struct.unpack_from('<6I',b,0);pos=0x18;s=fu;blocks=[(fc,fu)]
while s<ut:
 c,u=struct.unpack_from('<2I',b,pos);pos+=8;blocks.append((c,u));s+=u
print('blocks',len(blocks),'data',hex(pos),blocks[:3]);dpos=pos
for i,(c,u) in enumerate(blocks[:5]):print(i,c,u,b[dpos:dpos+16].hex(), 'zlib', b[dpos:dpos+2].hex());dpos+=c
