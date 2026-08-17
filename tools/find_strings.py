from pathlib import Path
p=Path(r'D:\GALGUNVV\work\nso\main.uncompressed'); b=p.read_bytes()
for s in [b'coalesced_int.bin',b'FZHTW.bin',b'jpn',b'kor',b'GG2Game']:
 pos=[]; start=0
 while True:
  i=b.find(s,start)
  if i<0:break
  pos.append(i);start=i+1
 print(s,pos[:20])
