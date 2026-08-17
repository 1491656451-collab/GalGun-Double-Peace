from pathlib import Path
import struct
b=Path(r'D:\GALGUNVV\work\nso\main.uncompressed').read_bytes(); targets=[0x19c23c5-0x100,0x19c23c5,0x19c22c5,0x19c2300]
for t in targets:
 hits=[]
 for fmt in ('<I','<Q'):
  raw=struct.pack(fmt,t)
  start=0
  while True:
   i=b.find(raw,start)
   if i<0:break
   hits.append((fmt,i));start=i+1
 print(hex(t),hits[:20])
