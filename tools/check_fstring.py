from pathlib import Path
b=Path(r'D:\GALGUNVV\work\raw_prologue\Common_Prologue_map\Common_Prologue\Text_Common_Prologue_CHT.GG2CollectionText').read_bytes()
for off in [0x5b,0x122,0x282]:
 print(hex(off),b[off:off+16].hex(), int.from_bytes(b[off:off+4],'little',signed=True))
 print('after',repr(b[off+4:off+4+40].decode('utf-16le','replace')))
