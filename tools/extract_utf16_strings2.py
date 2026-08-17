from pathlib import Path
for lang in ['CHT','ENG','JPN','KOR']:
 p=Path(r'D:\GALGUNVV\work\raw_prologue\Common_Prologue_map\Common_Prologue')/f'Text_Common_Prologue_{lang}.GG2CollectionText'
 b=p.read_bytes(); out=[]
 for off in range(0,len(b)-2,2):
  vals=[]; j=off
  while j+1<len(b):
   u=b[j]|(b[j+1]<<8)
   if u==0:break
   if u<0x20 and u not in (0x0A,0x0D,0x09):break
   vals.append(u);j+=2
  if len(vals)>=3 and j+1<len(b) and b[j]==0 and b[j+1]==0:
   s=''.join(chr(x) for x in vals)
   if any(ord(c)>127 for c in s) or any(c.isalpha() for c in s):out.append((off,s))
 chosen=[]
 for off,s in sorted(out,key=lambda x:(x[0],-len(x[1]))):
  if any(off>=o and off<o+len(t)*2 for o,t in chosen):continue
  chosen.append((off,s))
 Path(r'D:\GALGUNVV\work').joinpath(f'prologue_strings_{lang}.txt').write_text('\n'.join(f'{off:08X}\t{s}' for off,s in chosen),encoding='utf-8')
 Path(r'D:\GALGUNVV\work').joinpath(f'prologue_strings_{lang}.ascii.txt').write_text('\n'.join(f'{off:08X}\t{ascii(s)}' for off,s in chosen),encoding='ascii')
 print(lang,len(chosen))
