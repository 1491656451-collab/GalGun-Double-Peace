import struct
b=open(r'D:\GALGUNVV\work\nso\main.uncompressed','rb').read(0x100)
for off in range(0,0x70,4):print(hex(off),hex(struct.unpack_from('<I',b,off)[0]))
