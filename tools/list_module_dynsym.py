from pathlib import Path
import struct
for fn,dyn in [('sdk',0xcd4260),('subsdk0',0x576198),('subsdk1',0x9cc938)]:
 b=Path('work/nso_all/'+fn+'.uncompressed').read_bytes(); tags={}
 for i in range(200):
  tag,val=struct.unpack_from('<QQ',b,dyn+8+i*16); tags[tag]=val
  if tag==0:break
 so=tags[5]; ss=tags.get(10,0); sy=tags[6]; ent=tags[11]
 st=b[so:so+ss] if ss else b[so:so+0x100000]
 print('###',fn,'str',hex(so),'sym',hex(sy),'ent',ent,'strsz',hex(ss))
 for idx in range(50000):
  off=sy+idx*ent
  if off+24>len(b):break
  no,info,other,shnd=struct.unpack_from('<IBBH',b,off); val,size=struct.unpack_from('<QQ',b,off+8)
  if no>=len(st):continue
  e=st.find(b'\0',no); name=st[no:e].decode('latin1','replace')
  if any(x in name.lower() for x in ['aes','crypto','decrypt','encrypt','coalesced']):print(idx,hex(val),name)
