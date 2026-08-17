import sys,struct
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
b=open(r'D:\GALGUNVV\work\nso\main.uncompressed','rb').read()
text_end=0x1322000
targets=[0x19c23c5,0x19c23f5,0x19c32d3]
md=Cs(CS_ARCH_ARM64,CS_MODE_ARM); md.detail=True
ins=list(md.disasm(b[:text_end],0))
# find adrp page targets and nearby add/ldr refs
hits=[]
for idx,i in enumerate(ins):
 if i.mnemonic=='adrp':
  try:
   # op_str xN, #0x...
   target=int(i.op_str.split('#')[1],16)
  except: continue
  for t in targets:
   if target <= t < target+0x1000:
    hits.append((idx,i.address,i.mnemonic,i.op_str,t))
print('hits',len(hits))
for h in hits[:80]:
 idx,addr,_,op,t=h
 print('---',hex(addr),op,'target',hex(t))
 for j in ins[max(0,idx-2):idx+8]: print(hex(j.address),j.mnemonic,j.op_str)
