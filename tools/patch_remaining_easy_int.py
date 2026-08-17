from pathlib import Path
import json,re,shutil
ROOT=Path(r'D:\GALGUNVV'); source=json.loads((ROOT/'work/switch_cht_texts/all_switch_cht_texts_clean.json').read_text(encoding='utf-8'))
D=[ROOT/'steam/GG2Game/Localization/INT',Path(r'D:\SteamLibrary\steamapps\common\GalGun Double Peace/GG2Game/Localization/INT')]

def read_utf16(p):
 b=p.read_bytes(); return b[2:].decode('utf-16le') if b.startswith(b'\xff\xfe') else b.decode('utf-16le')
def write_utf16(p,s): p.write_bytes(b'\xff\xfe'+s.encode('utf-16le'))
def setf(line,f,v):
 pat=re.compile(rf'({f}=\")((?:\\.|[^"\\])*)(\")'); return pat.sub(lambda m:m.group(1)+v.replace('\\','\\\\').replace('"','\\"')+m.group(3),line,count=1)
def patch_pv(p):
 s=read_utf16(p); lines=s.splitlines(keepends=True); idx={int(re.match(r'Texts\[(\d+)\]',l).group(1)):i for i,l in enumerate(lines) if l.startswith('Texts[')}; pairs=source['Common_Prologue_map.xxx']['pairs']
 for n in range(min(45,len(pairs))):
  li=idx[n]; bare=lines[li].rstrip('\r\n'); bare=setf(bare,'Name',pairs[n]['name']); bare=setf(bare,'Text',pairs[n]['text']); lines[li]=bare+('\r\n' if lines[li].endswith('\r\n') else '\n')
 write_utf16(p,''.join(lines))
def patch_shino(p):
 raw=p.read_bytes(); s=raw.decode('cp932'); lines=s.splitlines(keepends=True); idx={int(re.match(r'Texts\[(\d+)\]',l).group(1)):i for i,l in enumerate(lines) if l.startswith('Texts[')}; pairs=source['Tutorial_ActionEvent_Shino_map.xxx']['pairs']
 # first 12 are dialogue slots; final pair is two selection strings.
 for n in range(12):
  li=idx[n]; bare=lines[li].rstrip('\r\n'); bare=setf(bare,'Name',pairs[n]['name']); bare=setf(bare,'Text',pairs[n]['text']); lines[li]=bare+('\r\n' if lines[li].endswith('\r\n') else '\n')
 selects=[n for n in idx if n>=0 and re.search(r'Label="SELECT',lines[idx[n]])]
 selects.sort()
 vals=[pairs[12]['text'],pairs[12]['name']]
 for n,v in zip(selects[:2],vals):
  li=idx[n]; bare=lines[li].rstrip('\r\n'); bare=setf(bare,'Text',v); lines[li]=bare+('\r\n' if lines[li].endswith('\r\n') else '\n')
 p.write_bytes(b'\xff\xfe'+''.join(lines).encode('utf-16le'))
for d in D:
 for base in ['Common_Prologue_PV','Common_Prologue_PV_ENG']:
  p=d/f'{base}.int'; backup=d/f'{base}.int.bak.switch_cht';
  if not backup.exists(): shutil.copy2(p,backup)
  patch_pv(p)
 p=d/'Tutorial_ActionEvent_Shinobu.int'; backup=d/'Tutorial_ActionEvent_Shinobu.int.bak.switch_cht';
 if not backup.exists(): shutil.copy2(p,backup)
 patch_shino(p)
print('patched PV and Shinobu special tutorial in staging and game')
