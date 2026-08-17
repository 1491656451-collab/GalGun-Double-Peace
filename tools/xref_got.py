import sys,re
from pathlib import Path
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=Path(r'work\nso\main.uncompressed').read_bytes();md=Cs(CS_ARCH_ARM64,CS_MODE_ARM);ins=list(md.disasm(b[0x200:0x1322100],0x100))
for idx,i in enumerate(ins):
 if i.mnemonic=='adrp' and '#0x1d7b000' in i.op_str:
  print('---',hex(i.address),i.op_str)
  for j in ins[idx:idx+8]:print(hex(j.address),j.mnemonic,j.op_str)
