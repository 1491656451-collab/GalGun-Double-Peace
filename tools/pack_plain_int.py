from pathlib import Path
import struct

def inv_utf16(s):
 n=len(s)
 return struct.pack('>I', (~n)&0xffffffff)+s.encode('utf-16le')+b'\0\0'

def decode(p):
 b=p.read_bytes()
 return (b[2:].decode('utf-16le') if b.startswith(b'\xff\xfe') else b.decode('cp932',errors='replace'))

def pack_file(w,p,base):
 rel=p.relative_to(base).as_posix().replace('/','\\')
 w.extend(inv_utf16('..\\'+rel))
 s=decode(p)
 sections=[]; cur=None
 for line in s.splitlines():
  if line.startswith('[') and ']' in line:
   cur={'name':line[1:line.index(']')],'pairs':[]}; sections.append(cur); continue
  if cur is None or not line or line.startswith(';') or line.startswith('#'): continue
  if '=' in line:
   k,v=line.split('=',1); cur['pairs'].append((k,v))
 w.extend(struct.pack('>I',len(sections)))
 for sec in sections:
  w.extend(inv_utf16(sec['name']))
  w.extend(struct.pack('>I',len(sec['pairs'])))
  for k,v in sec['pairs']:
   w.extend(inv_utf16(k));w.extend(inv_utf16(v))

base=Path(r'steam'); files=sorted((base/'GG2Game'/'Localization'/'INT').glob('*.int'))
w=bytearray(struct.pack('>I',len(files)))
for p in files:pack_file(w,p,base)
Path(r'work\pc_all_int_plain.bin').write_bytes(w)
print('files',len(files),'size',len(w),'cipher',Path(r'romfs\GG2Game\CookedNX\Coalesced_INT.bin').stat().st_size)
