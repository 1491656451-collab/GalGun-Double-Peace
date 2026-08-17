import sys,re
from pathlib import Path
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=Path(r'work\nso\main.uncompressed').read_bytes(); md=Cs(CS_ARCH_ARM64,CS_MODE_ARM); ins=list(md.disasm(b[0x200:0x1322100],0x100))
targets={0x19c23c5-0x100:'coal_int',0x19c23eb-0x100:'coal_jpn',0x19c2437-0x100:'coal_cht',0x18a81a3-0x100:'jpn'}
for idx,i in enumerate(ins):
 if i.mnemonic!='adrp': continue
 m=re.match(r'x(\d+), #0x([0-9a-f]+)',i.op_str)
 if not m: continue
 r=m.group(1); page=int(m.group(2),16)
 for j in ins[idx+1:idx+5]:
  if j.mnemonic=='add' and j.op_str.startswith(f'x{r}, x{r}, #0x'):
   addr=page+int(j.op_str.rsplit('#',1)[1],16)
   if addr in targets: print(targets[addr],hex(i.address),i.op_str,hex(j.address),j.op_str,hex(addr))
   break
