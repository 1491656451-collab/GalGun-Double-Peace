from pathlib import Path
import zlib,gzip,bz2,lzma
p=Path(r'D:\GALGUNVV\romfs\GG2Game\CookedNX\Coalesced_INT.bin')
b=p.read_bytes()
for off in [0,1,2,4,8,16,0x100,0x1000,0x1ed4f]:
 d=b[off:]
 for name,fn in [('zlib',zlib.decompress),('gzip',gzip.decompress),('bz2',bz2.decompress),('lzma',lzma.decompress)]:
  try:
   x=fn(d); print('OK',off,name,len(x),x[:40])
  except Exception: pass
print('try xor single-byte then zlib')
for k in range(256):
 d=bytes(x^k for x in b[:1024])
 for off in range(0,32):
  try:
   z=zlib.decompress(d[off:]); print('xor',k,off,len(z)); raise SystemExit
  except Exception: pass
