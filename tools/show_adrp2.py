import sys
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=open(r'D:\GALGUNVV\work\nso\main.uncompressed','rb').read(); md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
count=0
for i in md.disasm(b[0x200:0x100000],0x200):
 if i.mnemonic=='adrp':
  print(hex(i.address),i.mnemonic,i.op_str); count+=1
  if count>=20: break
print('count',count)
