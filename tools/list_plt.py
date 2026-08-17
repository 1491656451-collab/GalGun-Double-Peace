import sys
from pathlib import Path
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=Path(r'work\nso\main.uncompressed').read_bytes();md=Cs(CS_ARCH_ARM64,CS_MODE_ARM);ins=list(md.disasm(b[0x200:0x1322100],0x100));
for i in range(3,len(ins)):
 if ins[i].mnemonic=='br' and ins[i].op_str in ('x16','x17'):
  print('---',hex(ins[i].address));
  for j in ins[i-6:i+1]:print(hex(j.address),j.mnemonic,j.op_str)
