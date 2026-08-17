import sys
from pathlib import Path
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=Path(r'work\nso\main.uncompressed').read_bytes(); md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
stubs=[]
for off in range(0x100,0x1322100-20,4):
 ins=list(md.disasm(b[off:off+20],off-0x100))
 if len(ins)!=5:continue
 if [x.mnemonic for x in ins]==['stp','adrp','ldr','add','br'] and ins[-1].op_str=='x17':
  stubs.append((off,ins[2].op_str,ins[3].op_str))
print('count',len(stubs)); print(stubs[:5]);print(stubs[-5:])
for i,(off,ldr,add) in enumerate(stubs):
 if '#0x4f8' in ldr or '#0x4f8' in add: print('AES?',i,hex(off),ldr,add)
