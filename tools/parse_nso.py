import struct
p=r'D:\GALGUNVV\exefs\main'
b=open(p,'rb').read(0x100)
for off in range(0,0x80,4): print(hex(off),hex(struct.unpack_from('<I',b,off)[0]))
