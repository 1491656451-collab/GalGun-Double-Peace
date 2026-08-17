from pathlib import Path
for p in [Path(r'steam\GG2Game\Localization\INT\Kurona_ep7_5.int'),Path(r'D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\Localization\INT\Kurona_ep7_5.int')]:
 b=p.read_bytes(); s=b[2:].decode('utf-16le') if b.startswith(b'\xff\xfe') else b.decode('cp932')
 print(p, 'utf16bom', b.startswith(b'\xff\xfe'), 'texts', s.count('Texts['), 'jpn_chars', sum(1 for c in s if '\u3040' <= c <= '\u30ff'))
 for line in s.splitlines():
  if line.startswith('Texts[') and int(line.split('[',1)[1].split(']',1)[0]) < 10:
   print(line.encode('unicode_escape').decode())
