from pathlib import Path
import csv,re
roots=[Path(r"D:\GALGUNVV\steam\GG2Game\Localization\INT"),Path(r"D:\虚幻解包\GALGUN汉化源文件\GG2CNPatch\out\INT")]
for root in roots:
    chars=set(); files=0; textlines=0
    if root.exists():
      for p in root.glob('*.int'):
        files+=1
        try:s=p.read_text(encoding='utf-16')
        except: continue
        for ch in s:
          if '\u3000'<=ch<='\u9fff': chars.add(ch)
        textlines += len(re.findall(r'^Texts\[',s,re.M))
    print(root, 'files',files,'textlines',textlines,'cjk_unique',len(chars))
# translation csv unique chars
p=Path(r"D:\虚幻解包\GALGUN汉化源文件\GG2CNPatch\translations_int.csv")
chars=set(); rows=0
if p.exists():
  with p.open(encoding='utf-8-sig',newline='') as f:
    for row in csv.DictReader(f):
      rows+=1
      for k in ('zh_name','zh_text'):
        chars.update(ch for ch in row.get(k,'') if '\u3000'<=ch<='\u9fff')
print('csv rows',rows,'cjk_unique',len(chars))
print('missing sample',''.join(sorted(chars))[:200])
