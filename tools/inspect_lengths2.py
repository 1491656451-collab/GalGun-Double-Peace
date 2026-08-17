import json
from pathlib import Path
x=json.loads(Path(r'D:\GALGUNVV\work\switch_cht_texts\all_switch_cht_texts.json').read_text(encoding='utf-8'))
mx=[]
for fn,v in x.items():
 for p in v['pairs']:mx.append((len(p['text']),fn,p['text'][:200]))
out=['pairs '+str(len(mx))]
for item in sorted(mx,reverse=True)[:20]:out.append(repr(item))
Path(r'D:\GALGUNVV\work\lengths_ascii.txt').write_text('\n'.join(out),encoding='ascii',errors='backslashreplace')
