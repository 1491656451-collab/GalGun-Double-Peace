from pathlib import Path
import json,struct,subprocess,tempfile,shutil
idx=json.loads(Path(r'D:\GALGUNVV\work\cht_map_index.json').read_text(encoding='utf-8'))
name='Common_Prologue_map.xxx'; info=idx[name]
src=Path(r'D:\GALGUNVV\romfs\GG2Game\CookedNX')/name
tmp=Path(r'D:\GALGUNVV\work\one_map_tmp'); tmp.mkdir(exist_ok=True); out=tmp/name
subprocess.run([r'D:\虚幻解包\GALGUN汉化源文件\GG2CNPatch\tools\decompress\decompress.exe','-game=ue3',f'-out={tmp}',str(src)],check=True,capture_output=True)
b=out.read_bytes()[info['offset']:info['offset']+info['size']]
arr=[]
for off in range(len(b)-4):
 n=struct.unpack_from('<i',b,off)[0]
 if n<0 and -n<10000 and off+4+(-n)*2<=len(b):
  raw=b[off+4:off+4+(-n)*2]
  if raw[-2:]==b'\0\0':
   try:s=raw[:-2].decode('utf-16le')
   except:continue
   if all(not(0xD800<=ord(c)<=0xDFFF) for c in s):arr.append((off,s))
seen=set(); vals=[]
for off,s in arr:
 if off not in seen:seen.add(off);vals.append(s)
pairs=[{'name':vals[i+1] if i+1<len(vals) else '', 'text':vals[i]} for i in range(0,len(vals),2)]
print('vals',len(vals),'pairs',len(pairs));print(json.dumps(pairs[:3],ensure_ascii=False,indent=2));
