from pathlib import Path
import struct,sys,re
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=Path(r'work\nso\main.uncompressed').read_bytes();md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
# scan PLT stubs by raw offset, use output runtime address = raw - 0x100
stubs=[]
for off in range(0x1320300,0x1322100-16,4):
 ins=list(md.disasm(b[off:off+16],off-0x100))
 if len(ins)>=4 and ins[0].mnemonic in ('stp','adrp') and ins[-1].mnemonic=='br' and ins[-1].op_str=='x17':
  ldr=next((x for x in ins if x.mnemonic=='ldr' and x.op_str.startswith('x17')),None)
  if ldr:
   m=re.search(r'#0x([0-9a-f]+)',ldr.op_str); got=int(m.group(1),16) if m else 0
   page=int(re.search(r'#0x([0-9a-f]+)',next(x for x in ins if x.mnemonic=='adrp').op_str).group(1),16)
   stubs.append((off,off-0x100,page+got))
# exact AES reloc raw/runtime convention from main dynamic table
for name,got in [('ccm',0x1d7b3f8),('ccm_enc',0x1d7b408)]:
 xs=[x for x in stubs if x[2]==got]
 print(name,xs)
 if xs:
  target=xs[0][1]
  hits=[]
  for off in range(0x200,0x1322100,4):
   ins=list(md.disasm(b[off:off+4],off-0x100))
   if ins and ins[0].mnemonic=='bl' and ins[0].op_str==f'#0x{target:x}':hits.append((off,ins[0].address))
  print('calls',[(hex(a),hex(c)) for a,c in hits])
