from pathlib import Path
import sys,re
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=Path(r'work\nso\main.uncompressed').read_bytes();md=Cs(CS_ARCH_ARM64,CS_MODE_ARM);stubs=[]
for off in range(0x1320300,0x1322100-16,4):
 ins=list(md.disasm(b[off:off+16],off-0x100))
 if len(ins)!=4 or [x.mnemonic for x in ins]!=['adrp','ldr','add','br'] or ins[3].op_str!='x17':continue
 m1=re.search(r'#0x([0-9a-f]+)',ins[0].op_str);m2=re.search(r'#0x([0-9a-f]+)',ins[1].op_str)
 if not(m1 and m2):continue
 stubs.append((ins[0].address,int(m1.group(1),16)+int(m2.group(1),16)))
print('stubs',len(stubs));print('target',[(hex(a),hex(g)) for a,g in stubs if g==0x1d7b3f8])
