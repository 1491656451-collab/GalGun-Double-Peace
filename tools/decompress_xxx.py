from pathlib import Path
import struct,zlib,sys
src=Path(sys.argv[1]); out=Path(sys.argv[2]); b=src.read_bytes();
magic,ver,comp_total,unc_total,first_c,first_u=struct.unpack_from('<6I',b,0)
assert magic==0x9e2A83C1,hex(magic)
blocks=[(first_c,first_u)]; s=first_u; pos=0x18
while s<unc_total:
 c,u=struct.unpack_from('<2I',b,pos); pos+=8; blocks.append((c,u)); s+=u
outdata=bytearray(); dpos=pos
for i,(c,u) in enumerate(blocks):
 chunk=b[dpos:dpos+c]; dpos+=c
 raw=zlib.decompress(chunk)
 if len(raw)!=u: raise RuntimeError((i,len(raw),u))
 outdata.extend(raw)
print(src.name,'blocks',len(blocks),'out',len(outdata),'expected',unc_total,'dataOffset',hex(pos))
out.write_bytes(outdata)
