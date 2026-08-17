import struct
from pathlib import Path
b=Path(r'work\nso\main.uncompressed').read_bytes()
base=0x100
for rt,name in [(0x188ecc8,'str'),(0x188c6d0,'sym'),(0x1889810,'jmprel'),(0x1322048,'rela')]:
 off=rt+base; print(name,hex(off),b[off:off+64].hex(' '),b[off:off+128].decode('latin1',errors='replace').encode('unicode_escape').decode())
