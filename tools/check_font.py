from pathlib import Path
import struct
p=Path(r"D:\GALGUNVV\work\MessageFont.Font")
x=p.read_bytes(); cc=struct.unpack_from("<i",x,0x1c)[0]; marker=struct.pack("<ii",80,0); expected=12+cc*4; remap=None
for off in range(len(x)-expected,0,-1):
    if x[off:off+8]==marker and struct.unpack_from("<i",x,off+8)[0]==cc:
        remap=off+12;break
codes=[struct.unpack_from("<I",x,remap+i*4)[0]&0xffff for i in range(cc)]
chars="\u55ce\u54e6\u6703\u4f1a\u5b78\u5b66\u5712\u56ed\u8cfc\u8d2d\u8cb7\u4e70\u9084\u8fd8\u771f\u5c11\u898b\u89c1\u4f60\u5011\u4eec\u5169\u4e2a\u500b\u8a8d\u8bc6\u55ce\u5417\u55ef\u5979\u540c\u73ed\u6a02\u4e50\u968a\u961f\u5f48\u5f39\u5409\u5409\u4ed6\u88e1\u91cc\u5b78\u6821\u6821\u633a\u6709\u540d\u70ba\u4e3a\u6512\u6512\u8cc7\u8d44\u9019\u8fd9\u6240\u4e0d\u77e5\u9ebc\u4e48\u6c23\u6c14\u5834\u573a\u5f71\u97ff\u54cd\u96e3\u96be\u9053\u60e1\u6076\u9b54\u7375\u730e\u4eba\u4ed4\u7d30\u7ec6\u8aaa\u8bf4\u660e\u6709\u6642\u65f6\u5019\u666e\u901a\u4eba\u4e5f\u4e0d\u6703\u4f1a\u53d7\u5230\u4f60"
for ch in chars:
    print(f"U+{ord(ch):04X}\t{'yes' if ord(ch) in codes else 'no'}")
print('char_count',cc,'remap_offset',remap)
