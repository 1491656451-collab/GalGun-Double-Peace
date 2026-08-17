from pathlib import Path
b=Path(r'D:\GALGUNVV\work\nso\main.uncompressed').read_bytes()[:64]
print(' '.join(f'{x:02X}' for x in b))
