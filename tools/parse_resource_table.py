from pathlib import Path
import re
b=Path(r'work\nso\main.uncompressed').read_bytes()
start=0x19c23c5
end=0x19c25b0
p=start
while p<end:
 q=b.find(b'\0',p)
 if q<0:break
 name=b[p:q]
 p=q+1
 if not name: continue
 if p+16>end:break
 val=b[p:p+20]; p+=20
 print(name.decode('ascii'), val.hex())
