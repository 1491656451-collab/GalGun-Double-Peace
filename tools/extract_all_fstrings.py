from pathlib import Path
import struct,json
base=Path(r'D:\GALGUNVV\work\raw_prologue\Common_Prologue_map\Common_Prologue')
for lang in ['CHT','JPN','KOR']:
 b=(base/f'Text_Common_Prologue_{lang}.GG2CollectionText').read_bytes(); arr=[]
 for off in range(len(b)-4):
  n=struct.unpack_from('<i',b,off)[0]
  if n<0 and -n<10000 and off+4+(-n)*2<=len(b):
   raw=b[off+4:off+4+(-n)*2]
   if raw[-2:]==b'\0\0':
    try:s=raw[:-2].decode('utf-16le')
    except:continue
    if all(not(0xD800<=ord(c)<=0xDFFF) for c in s): arr.append({'off':off,'len':-n,'text':s})
 # unique offset
 seen=set(); out=[]
 for x in arr:
  if x['off'] not in seen:seen.add(x['off']);out.append(x)
 (Path(r'D:\GALGUNVV\work')/f'fstrings_all_{lang}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(lang,len(out))
