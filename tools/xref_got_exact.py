import sys,re
from pathlib import Path
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=Path(r'work\nso\main.uncompressed').read_bytes();md=Cs(CS_ARCH_ARM64,CS_MODE_ARM);ins=list(md.disasm(b[0x200:0x1322100],0x100))
target=0x1d7b3f8
for idx,i in enumerate(ins):
 if i.mnemonic!='adrp':continue
 m=re.match(r'x(\d+), #0x([0-9a-f]+)',i.op_str)
 if not m:continue
 r=m.group(1);base=int(m.group(2),16)
 for j in range(idx+1,min(idx+8,len(ins))):
  x=ins[j]
  if x.mnemonic in ('add','sub') and x.op_str.startswith(f'x{r}, x{r}, #0x'):
   sign=-1 if x.mnemonic=='sub' else 1; base2=base+sign*int(x.op_str.rsplit('#',1)[1],16)
   if base2==target: print('ADD',hex(i.address),i.op_str,hex(x.address),x.op_str)
  if x.mnemonic=='ldr' and ('['+f'x{r}' in x.op_str or '['+f'w{r}' in x.op_str):
   mm=re.search(r'#0x([0-9a-f]+)',x.op_str); off=int(mm.group(1),16) if mm else 0
   if base+off==target: print('LDR',hex(i.address),i.op_str,hex(x.address),x.op_str)
