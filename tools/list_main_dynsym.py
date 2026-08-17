from pathlib import Path
import struct
b=Path(r'work\nso\main.uncompressed').read_bytes(); base=0x100
str_off=0x188ecc8+base; sym_off=0x188c6d0+base; syment=24; strtab=b[str_off:str_off+0x3846]
for idx in range(0,20000):
 off=sym_off+idx*syment
 if off+24>len(b):break
 nameoff,info,other,shndx=struct.unpack_from('<IBBH',b,off); val,size=struct.unpack_from('<QQ',b,off+8)
 if nameoff>=len(strtab): continue
 name=strtab[nameoff:strtab.find(b'\0',nameoff)].decode('latin1',errors='replace')
 if any(x in name.lower() for x in ['crypto','aes','encrypt','decrypt','coalesc','archive','filemanager']):
  print(idx,hex(off),info,shndx,hex(val),hex(size),name)
