from pathlib import Path
b=Path(r'D:\GALGUNVV\work\nso\main.uncompressed').read_bytes()
for s in [b'coalesced_int.bin',b'FZHTW.bin',b'jpn',b'kor']:
 print(s,[hex(i) for i in [b.find(s)]])
