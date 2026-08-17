from pathlib import Path
b=Path(r'D:\GALGUNVV\work\raw_prologue\Common_Prologue_map\Common_Prologue\Text_Common_Prologue_CHT.GG2CollectionText').read_bytes()
out=[]
for off in [0x70,0x80,0x90,0xA0]:
 d=b[off:off+160]
 out.append(f'off {off:x} utf16le {d.decode("utf-16le","replace")[:80]!r}')
 out.append(f'utf16be {d.decode("utf-16be","replace")[:80]!r}')
 out.append(f'utf8 {d.decode("utf-8","replace")[:80]!r}')
Path(r'D:\GALGUNVV\work\decode_raw_out.txt').write_text('\n'.join(out),encoding='ascii',errors='backslashreplace')
