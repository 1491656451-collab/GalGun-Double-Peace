from pathlib import Path
import struct
b=Path(r'work/nso/main.uncompressed').read_bytes();base=0x100
rel_off=0x1889810+base; rel_sz=0x2118
for i in range(rel_sz//24):
 off=rel_off+i*24; ro,info,add=struct.unpack_from('<QQq',b,off); sym=info>>32;typ=info&0xffffffff
 if sym in [290,292,182]: print('entry',i,'sym',sym,'type',typ,'offset',hex(ro),'raw',hex(ro+base),'add',add)
