from pathlib import Path
import json,struct,subprocess,shutil,sys,time
idx=json.loads(Path(r'D:\GALGUNVV\work\cht_map_index.json').read_text(encoding='utf-8'))
srcroot=Path(r'D:\GALGUNVV\romfs\GG2Game\CookedNX'); tmp=Path(r'D:\GALGUNVV\work\batch_map_tmp'); outroot=Path(r'D:\GALGUNVV\work\switch_cht_texts'); tmp.mkdir(exist_ok=True); outroot.mkdir(exist_ok=True)
dec=r'D:\虚幻解包\GALGUN汉化源文件\GG2CNPatch\tools\decompress\decompress.exe'
allout={}; failures=[]
for num,(name,info) in enumerate(sorted(idx.items()),1):
 src=srcroot/name; outfile=tmp/name
 try:
  if outfile.exists(): outfile.unlink()
  p=subprocess.run([dec,'-game=ue3',f'-out={tmp}',str(src)],capture_output=True,text=True,timeout=120)
  if p.returncode!=0 or not outfile.exists(): raise RuntimeError((p.returncode,p.stderr[-500:]))
  b=outfile.read_bytes()[info['offset']:info['offset']+info['size']]
  vals=[]
  for off in range(len(b)-4):
   n=struct.unpack_from('<i',b,off)[0]
   if n<0 and -n<10000 and off+4+(-n)*2<=len(b):
    raw=b[off+4:off+4+(-n)*2]
    if raw[-2:]==b'\0\0':
     try:s=raw[:-2].decode('utf-16le')
     except:continue
     if all(not(0xD800<=ord(c)<=0xDFFF) for c in s): vals.append((off,s))
  seen=set(); strings=[]
  for off,s in vals:
   if off not in seen:seen.add(off);strings.append(s)
  pairs=[{'name':strings[i+1] if i+1<len(strings) else '', 'text':strings[i]} for i in range(0,len(strings),2)]
  allout[name]={'object':info['object'],'pairs':pairs,'string_count':len(strings)}
  if num%10==0: print('processed',num,'pairs',sum(len(v['pairs']) for v in allout.values()),flush=True)
 except Exception as e:
  failures.append({'file':name,'error':repr(e)})
  print('FAIL',name,repr(e),flush=True)
 if outfile.exists(): outfile.unlink()
(outroot/'all_switch_cht_texts.json').write_text(json.dumps(allout,ensure_ascii=False,indent=2),encoding='utf-8')
(outroot/'failures.json').write_text(json.dumps(failures,ensure_ascii=False,indent=2),encoding='utf-8')
print('done files',len(allout),'failures',len(failures),'pairs',sum(len(v['pairs']) for v in allout.values()))
