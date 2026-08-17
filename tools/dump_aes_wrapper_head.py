import sys
sys.path.insert(0,r'D:\GALGUNVV\tools\python_pkgs')
from capstone import *
b=open(r'work\nso\main.uncompressed','rb').read();md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
for i in md.disasm(b[0x131d900:0x131e100],0x131d800): print(hex(i.address),i.mnemonic,i.op_str)
