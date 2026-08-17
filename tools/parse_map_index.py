from pathlib import Path
import re,json
log=Path(r'D:\GALGUNVV\work\all_map_text_objects.txt').read_text(encoding='utf-8',errors='replace')
cur=None; out={}
for line in log.splitlines():
 if line.startswith('### '):cur=line[4:].strip()
 m=re.search(r'\s+\d+\s+([0-9A-F]+)\s+([0-9A-F]+)\s+GG2CollectionText\s+(Text_.*_CHT)$',line)
 if m and cur: out[cur]={'offset':int(m.group(1),16),'size':int(m.group(2),16),'object':m.group(3)}
print('count',len(out)); print(list(out.items())[:5]); Path(r'D:\GALGUNVV\work\cht_map_index.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
