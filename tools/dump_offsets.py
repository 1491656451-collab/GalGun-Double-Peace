from pathlib import Path
b=Path(r'D:\GALGUNVV\work\nso\main.uncompressed').read_bytes()
for off in [0x100,0x200,0x1000,0x10000,0x1322100]:print(hex(off),' '.join(f'{x:02X}' for x in b[off:off+32]))
