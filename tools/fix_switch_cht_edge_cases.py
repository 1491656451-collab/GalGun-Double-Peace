from pathlib import Path
import json,re

ROOT=Path(r'D:\GALGUNVV')
SRC=json.loads((ROOT/'work/switch_cht_texts/all_switch_cht_texts_clean.json').read_text(encoding='utf-8'))
TARGETS=[ROOT/'steam/GG2Game/Localization/INT', ROOT/'work/pc_cht_patch/GG2Game/Localization/INT']

def read(p):
 b=p.read_bytes(); return (b'\xff\xfe',b[2:].decode('utf-16le')) if b.startswith(b'\xff\xfe') else (b'',b.decode('utf-16le'))
def write(p,s,bom): p.write_bytes(bom+s.encode('utf-16le'))
def setfield(line,field,value):
 value=value.replace('\\','\\\\').replace('"','\\"')
 pat=re.compile(rf'({field}=\")((?:\\.|[^"\\])*)(\")')
 if pat.search(line): return pat.sub(lambda m:m.group(1)+value+m.group(3),line,count=1)
 return line

def patch_file(path,base,updates):
 bom,s=read(path); lines=s.splitlines(keepends=True); idx={}
 for i,line in enumerate(lines):
  m=re.match(r'Texts\[(\d+)\]',line)
  if m: idx[int(m.group(1))]=i
 for n,vals in updates.items():
  if n not in idx: raise RuntimeError((path,n))
  li=idx[n]; bare=lines[li].rstrip('\r\n')
  if 'text' in vals: bare=setfield(bare,'Text',vals['text'])
  if 'name' in vals: bare=setfield(bare,'Name',vals['name'])
  if vals.get('clear_name'): bare=setfield(bare,'Name','')
  if vals.get('clear_text'): bare=setfield(bare,'Text','')
  nl='\r\n' if lines[li].endswith('\r\n') else '\n'; lines[li]=bare+nl
 write(path,''.join(lines),bom)

# Maya_ep5_4 has a PC-only debug/result slot layout. The Switch object stores
# the same tail as [debug, extra debug text, speaker, big-success, ...], while
# PC stores the speaker/result on one Text slot and has ten SELECT slots.
v=SRC['Maya_ep5_4_map.xxx']['pairs']
u={}
for i in range(62): u[i]={'text':v[i]['text'],'name':v[i]['name']}
u[62]={'text':v[62]['text']}                 # keep PC Name=NONE
u[63]={'text':v[63]['name'],'name':v[63]['text']}
u[64]={'text':v[64]['text']}
u[65]={'text':v[64]['name']}
u[66]={'text':v[64]['name']}
u[67]={'text':''}; u[68]={'text':''}
u[69]={'text':v[65]['text']}; u[70]={'text':v[65]['name']}
u[71]={'text':v[66]['text']}; u[72]={'text':v[66]['name']}; u[73]={'text':v[67]['text']}
# Sisters_ep3_3 has four PC branch copies of the same "start" line; Switch
# stores one copy. Reuse it at TEXT30A/B/C/D and map the remaining records by
# their original Switch order.
v2=SRC['Sisters_ep3_3_map.xxx']['pairs']; u2={}
for i in range(15): u2[i]={'text':v2[i]['text'],'name':v2[i]['name']}
start={'text':v2[29]['text'],'name':v2[29]['name']}
for n in (15,20,24,32): u2[n]=start
mapping={16:15,17:16,18:17,19:18,21:19,22:20,23:21,25:22,26:23,27:24,28:25,29:26,30:27,31:28,33:30,34:31,35:32,36:33,37:34,38:35,39:36}
for target,src in mapping.items(): u2[target]={'text':v2[src]['text'],'name':v2[src]['name']}
u2[40]={'text':''}
u2[41]={'text':v2[37]['text']}; u2[42]={'text':v2[37]['name']}; u2[43]={'text':v2[38]['text']}; u2[44]={'text':v2[38]['name']}; u2[45]={'text':v2[39]['text']}
# Sisters_End_true is one-to-one except the final combined speaker name.
v3=SRC['Sisters_End_true_map.xxx']['pairs']; u3={i:{'text':p['text'],'name':p['name']} for i,p in enumerate(v3[:46])}; u3[46]={'text':'','name':''}
for target_dir in TARGETS:
 for suffix in ('_ENG', ''):
  patch_file(target_dir/f'Maya_ep5_4{suffix}.int','Maya_ep5_4',u)
  patch_file(target_dir/f'Sisters_ep3_3{suffix}.int','Sisters_ep3_3',u2)
  patch_file(target_dir/f'Sisters_End_true{suffix}.int','Sisters_End_true',u3)
print('fixed edge-case mappings in',len(TARGETS),'targets and both INT suffixes')
