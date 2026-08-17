from pathlib import Path
import struct

def lz4_raw(data, out_len):
    out=bytearray(); i=0
    while i<len(data):
        token=data[i]; i+=1
        lit=token>>4
        if lit==15:
            while True:
                n=data[i];i+=1;lit+=n
                if n!=255:break
        out.extend(data[i:i+lit]);i+=lit
        if i>=len(data):break
        off=data[i]|(data[i+1]<<8);i+=2
        m=(token&15)+4
        if (token&15)==15:
            while True:
                n=data[i];i+=1;m+=n
                if n!=255:break
        start=len(out)-off
        if start<0: raise ValueError(('bad offset',i,off,len(out)))
        for j in range(m): out.append(out[start+j])
    if len(out)!=out_len: raise ValueError(('size',len(out),out_len))
    return bytes(out)

def nso_uncomp(src,dst):
 b=Path(src).read_bytes(); assert b[:4]==b'NSO0'
 segs=[]
 for idx,fo in enumerate([0x10,0x20,0x30]):
  file_off=struct.unpack_from('<I',b,fo)[0]
  mem_off=struct.unpack_from('<I',b,fo+4)[0]
  dec_size=struct.unpack_from('<I',b,fo+8)[0]
  comp_size=struct.unpack_from('<I',b,0x60+idx*4)[0]
  segs.append((file_off,mem_off,comp_size,dec_size))
 print(src,segs)
 total=max(m+d for f,m,c,d in segs)
 out=bytearray(total)
 for f,m,c,d in segs:
  raw=b[f:f+c]
  x=raw if c==d else lz4_raw(raw,d)
  out[m:m+d]=x
 Path(dst).write_bytes(out)
 print('wrote',dst,len(out))

if __name__=='__main__':
 import sys
 nso_uncomp(sys.argv[1],sys.argv[2])
