import sys
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=open(r'D:\GALGUNVV\work\nso\main.uncompressed','rb').read(); text_end=0x1322100
# runtime VA of rodata bytes is file offset - 0x100 in this hactool image
targets=[(0x19c23c5-0x100,'coal'),(0x18c19a0-0x100,'fz'),(0x18a81a3-0x100,'jpn'),(0x18c78a0-0x100,'kor')]
md=Cs(CS_ARCH_ARM64,CS_MODE_ARM); md.detail=True
ins=list(md.disasm(b[0x200:text_end],0x200))
hits=[]
for idx,i in enumerate(ins):
 if i.mnemonic=='adrp':
  try: target=int(i.op_str.split('#')[1],16)
  except: continue
  for t,n in targets:
   if target <= t < target+0x1000: hits.append((idx,i.address,i.op_str,t,n))
print('hits',len(hits))
for idx,addr,op,t,n in hits[:100]:
 print('---',n,hex(addr),op,'target',hex(t))
 for j in ins[max(0,idx-3):idx+9]: print(hex(j.address),j.mnemonic,j.op_str)
