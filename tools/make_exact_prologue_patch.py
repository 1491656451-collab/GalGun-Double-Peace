from pathlib import Path
import json,re,shutil
src=Path(r'D:\GALGUNVV\steam\GG2Game\Localization\INT\Common_Prologue_ENG.int')
cht=json.loads(Path(r'D:\GALGUNVV\work\fstrings_all_CHT.json').read_text(encoding='utf-8'))
pairs=[(cht[i+1]['text'],cht[i]['text']) for i in range(0,len(cht),2)]
print('CHT pairs',len(pairs))
text=src.read_text(encoding='utf-16')
line_re=re.compile(r'^(Texts\[(\d+)\]=\(.*)$')
field_re=re.compile(r'(?P<key>Name|Text)="(?P<value>(?:[^"\\]|\\.)*)"')
count=0
out=[]
for line in text.splitlines(keepends=True):
 m=line_re.match(line)
 if not m:
  out.append(line); continue
 idx=int(m.group(2))
 if idx < len(pairs):
  name,val=pairs[idx]
  def repl(mm):
   key=mm.group('key'); value=name if key=='Name' else val
   value=value.replace('\\',r'\\').replace('"',r'\"')
   return f'{key}="{value}"'
  line=field_re.sub(repl,line)
  count+=1
 out.append(line)
patched=''.join(out)
root=Path(r'D:\GALGUNVV\test_patch_switch_prologue_exact')
loc=root/'GG2Game'/'Localization'/'INT'; cooked=root/'GG2Game'/'CookedPC'
loc.mkdir(parents=True,exist_ok=True); cooked.mkdir(parents=True,exist_ok=True)
for n in ('Common_Prologue.int','Common_Prologue_ENG.int'):(loc/n).write_text(patched,encoding='utf-16')
chars=''.join(sorted({ch for _,v in pairs for ch in (v) if '\u3000'<=ch<='\u9fff'} | {ch for n,v in pairs for ch in n if '\u3000'<=ch<='\u9fff'}))
Path(r'D:\GALGUNVV\work\switch_prologue_cht_chars.txt').write_text(chars,encoding='utf-8')
shutil.copy2(r'D:\GALGUNVV\work\cht_prologue_font_output\Startup_LOC_INT.cht_prologue.upk',cooked/'Startup_LOC_INT.upk')
(root/'README.txt').write_text('Exact Switch CHT Common_Prologue test patch.\n\nText source: Switch Common_Prologue_map.xxx Text_Common_Prologue_CHT.\nFiles: Common_Prologue.int, Common_Prologue_ENG.int, and PC-compatible font package.\nDo not replace CharTextures.tfc. Back up originals before testing.\n',encoding='utf-8')
print('replaced',count,'chars',len(chars))
