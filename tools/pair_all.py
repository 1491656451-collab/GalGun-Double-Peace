import json
from pathlib import Path
x=json.loads(Path(r'D:\GALGUNVV\work\fstrings_all_CHT.json').read_text(encoding='utf-8'))
out=[]
for i in range(0,len(x),2):
 t=x[i]['text']; n=x[i+1]['text'] if i+1<len(x) else ''
 out.append(f'{i//2:02d}\tNAME={n}\tTEXT={t}')
Path(r'D:\GALGUNVV\work\cht_pairs_all.txt').write_text('\n'.join(out),encoding='utf-8')
