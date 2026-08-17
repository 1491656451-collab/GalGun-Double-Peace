from pathlib import Path
import struct
b=Path(r'D:\GALGUNVV\work\raw_prologue\Common_Prologue_map\Common_Prologue\Text_Common_Prologue_CHT.GG2CollectionText').read_bytes()
for off in range(len(b)-4):
 n=struct.unpack_from('<i',b,off)[0]
 if n<0 and -n<10000 and off+4+(-n)*2<=len(b):
  # try length -n includes terminator
  raw=b[off+4:off+4+(-n)*2]
  if raw[-2:]==b'\x00\x00':
   try:s=raw[:-2].decode('utf-16le')
   except:continue
   if any(ord(c)>=0x3000 for c in s) or any(c.isalpha() for c in s): print(hex(off),n,repr(s[:100]))
