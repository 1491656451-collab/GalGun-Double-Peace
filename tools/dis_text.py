import sys
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=open(r'D:\GALGUNVV\work\nso\main.uncompressed','rb').read(); md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
for i in list(md.disasm(b[0x100:0x300],0x100))[:80]: print(hex(i.address),i.mnemonic,i.op_str)
