from pathlib import Path
import csv
for name,fields in [('translations_int.csv',['zh_name','zh_text']),('ui_translations_int.csv',['zh'])]:
 p=Path(r'D:\虚幻解包\GALGUN汉化源文件\GG2CNPatch')/name
 chars=set(); rows=0
 with p.open(encoding='utf-8-sig',newline='') as f:
  for row in csv.DictReader(f):
   rows+=1
   for k in fields: chars.update(ch for ch in row.get(k,'') if '\u3000'<=ch<='\u9fff')
 print(name,rows,len(chars))
print('union')
chars=set()
for name,fields in [('translations_int.csv',['zh_name','zh_text']),('ui_translations_int.csv',['zh'])]:
 p=Path(r'D:\虚幻解包\GALGUN汉化源文件\GG2CNPatch')/name
 with p.open(encoding='utf-8-sig',newline='') as f:
  for row in csv.DictReader(f):
   for k in fields: chars.update(ch for ch in row.get(k,'') if '\u3000'<=ch<='\u9fff')
print(len(chars))
