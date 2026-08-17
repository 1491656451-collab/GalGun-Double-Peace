from pathlib import Path
s=Path(r'steam\GG2Game\Localization\INT\Kurona_ep7_5.int').read_bytes().decode('cp932')
for i,l in enumerate(s.splitlines()):
 print(f'{i:03}: {l.encode("unicode_escape").decode()}')
