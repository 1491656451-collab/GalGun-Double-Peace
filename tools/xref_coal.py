import sys
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=open(r'D:\GALGUNVV\work\nso\main.uncompressed','rb').read(); text_end=0x1322100; t=0x19c23c5-0x100
md=Cs(CS_ARCH_ARM64,CS_MODE_ARM); ins=list(md.disasm(b[0x200:text_end],0x200))
for idx,i in enumerate(ins):
 if i.mnemonic=='adrp':
  try: tar=int(i.op_str.split('#')[1],16)
  except: continue
  if tar<=t<tar+0x1000:
   print('HIT',hex(i.address),i.op_str,'target',hex(t))
   for j in ins[max(0,idx-10):idx+20]:print(hex(j.address),j.mnemonic,j.op_str)
