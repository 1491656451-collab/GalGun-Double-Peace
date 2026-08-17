from pathlib import Path
import struct,json,configparser

src=Path(r'D:\GALGUNVV\romfs\GG2Game\CookedNX\Coalesced_INT.bin'); out=Path(r'D:\GALGUNVV\work\coalesced_int_unpack'); out.mkdir(parents=True,exist_ok=True)
b=src.read_bytes(); pos=0

def u32():
 global pos
 if pos+4>len(b): raise EOFError(pos)
 v=struct.unpack_from('>I',b,pos)[0]; pos+=4; return v

def s16():
 global pos
 n=u32()
 if n in (0,0xffffffff): return ''
 n=(~n)&0xffffffff; size=n*2+2
 if pos+size>len(b): raise EOFError((pos,n,len(b)))
 raw=b[pos:pos+n*2]; pos+=size
 return raw.decode('utf-16le')
count=u32(); print('filecount',count)
files=[]
for fi in range(count):
 name=s16(); sc=u32(); sections=[]
 for si in range(sc):
  sec=s16(); vc=u32(); vals=[]
  for vi in range(vc): vals.append((s16(),s16()))
  sections.append((sec,vals))
 files.append((name,sections))
 print(fi,name,'sections',sc)
for name,sections in files:
 rel=name
 # common prefix ..\\ etc
 rel=rel.replace('..\\','').replace('\\','/')
 p=out/rel; p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  for sec,vals in sections:
   f.write(f'[{sec}]\n')
   for k,v in vals:
    f.write(f'{k}={v}\n')
   f.write('\n')
(out/'_metadata.json').write_text(json.dumps({'file_count':count,'bytes_consumed':pos,'bytes_total':len(b),'files':[n for n,_ in files]},ensure_ascii=False,indent=2),encoding='utf-8')
print('done',pos,len(b))
