from pathlib import Path
import sys,re
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=Path(r'work\nso\main.uncompressed').read_bytes();md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
ins=list(md.disasm(b[0x200:0x1322100],0x100)); by={i.address:i for i in ins}
stubs=[]
for off in range(0x1320300,0x1322100-16,4):
 addr=off-0x100; a=by.get(addr); b1=by.get(addr+4); c=by.get(addr+8); d=by.get(addr+12)
 if not all((a,b1,c,d)):continue
 if d.mnemonic!='br' or d.op_str!='x17':continue
 if c.mnemonic!='ldr' or not c.op_str.startswith('x17'):continue
 m=re.search(r'#0x([0-9a-f]+)',c.op_str); n=re.search(r'#0x([0-9a-f]+)',b1.op_str); 
 if m and n:stubs.append((addr,int(n.group(1),16)+int(m.group(1),16)))
print('stubs',len(stubs))
for name,got in [('ccm',0x1d7b3f8),('ccm_enc',0x1d7b408)]:
 xs=[x for x in stubs if x[1]==got];print(name,xs)
 if xs:
  target=xs[0][0];print('calls',[(hex(i.address),i.op_str) for i in ins if i.mnemonic=='bl' and i.op_str==f'#0x{target:x}'])
