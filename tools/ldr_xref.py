import sys
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=open(r'D:\GALGUNVV\work\nso\main.uncompressed','rb').read(); t=0x19c23c5-0x100; md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
for i in md.disasm(b[0x200:0x1322100],0x200):
 if i.mnemonic=='ldr' and '#' in i.op_str:
  try:
   tar=int(i.op_str.split('#')[1],16)
   if abs(tar-t)<0x1000: print(hex(i.address),i.op_str)
  except: pass
