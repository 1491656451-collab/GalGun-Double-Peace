from pathlib import Path
b=Path(r'D:\GALGUNVV\work\raw_prologue\Common_Prologue_map\Common_Prologue\Text_Common_Prologue_CHT.GG2CollectionText').read_bytes()
for off in range(0x40,0x150,4):
 print(f'{off:04X}',b[off:off+4].hex(), int.from_bytes(b[off:off+4],'little'))
