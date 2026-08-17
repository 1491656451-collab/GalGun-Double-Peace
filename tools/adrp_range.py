import sys
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=open(r'D:\GALGUNVV\work\nso\main.uncompressed','rb').read();md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
count=0
for i in md.disasm(b[0x200:0x1322100],0x200):
 if i.mnemonic=='adrp':
  try: tar=int(i.op_str.split('#')[1],16)
  except: continue
  if 0x19c0000<=tar<=0x19c4000:
   print(hex(i.address),i.op_str);count+=1
print(count)
