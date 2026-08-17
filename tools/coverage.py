from pathlib import Path
import struct,csv
p=Path(r'D:\GALGUNVV\work\MessageFont.Font'); x=p.read_bytes(); cc=struct.unpack_from('<i',x,0x1c)[0]; marker=struct.pack('<ii',80,0); exp=12+cc*4; off=None
for i in range(len(x)-exp,0,-1):
 if x[i:i+8]==marker and struct.unpack_from('<i',x,i+8)[0]==cc: off=i+12; break
codes={struct.unpack_from('<I',x,off+i*4)[0]&0xffff for i in range(cc)}
sets={}
for name,fields in [('story',['zh_name','zh_text']),('ui',['zh']),('union',['zh_name','zh_text','zh'])]:
 chars=set()
 for fn,fs in [('translations_int.csv',['zh_name','zh_text']),('ui_translations_int.csv',['zh'])]:
  if name=='story' and fn!='translations_int.csv': continue
  if name=='ui' and fn!='ui_translations_int.csv': continue
  pp=Path(r'D:\虚幻解包\GALGUN汉化源文件\GG2CNPatch')/fn
  with pp.open(encoding='utf-8-sig',newline='') as f:
   for row in csv.DictReader(f):
    for k in fs: chars.update(ch for ch in row.get(k,'') if '\u3000'<=ch<='\u9fff')
 sets[name]=chars
for k,s in sets.items(): print(k,'total',len(s),'already',len(s & {chr(c) for c in codes}),'missing',len(s-{chr(c) for c in codes}))
print('font_records',cc,'ascii_protected_estimate',105,'usable',cc-105)
