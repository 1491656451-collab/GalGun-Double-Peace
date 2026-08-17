from pathlib import Path
for label,p in [('bak',Path(r'steam\GG2Game\Localization\INT\Kurona_ep7_5.int.bak.switch_cht')),('now',Path(r'steam\GG2Game\Localization\INT\Kurona_ep7_5.int'))]:
 b=p.read_bytes(); s=(b[2:].decode('utf-16le') if b.startswith(b'\xff\xfe') else b.decode('cp932'))
 print(label)
 for x in s.splitlines():
  if x.startswith('Texts[0]') or x.startswith('DemoScripts[4]') or (x.startswith(' ') and 'きり' in x): print(x.encode('unicode_escape').decode())
