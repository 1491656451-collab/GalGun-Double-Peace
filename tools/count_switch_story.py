from pathlib import Path
import json
j=json.loads(Path(r'D:\GALGUNVV\work\switch_cht_texts\all_switch_cht_texts.json').read_text(encoding='utf-8'))
chars=set(); total=0
for v in j.values():
 for p in v['pairs']:
  total+=1
  chars.update(ch for ch in p['name']+p['text'] if '\u3000'<=ch<='\u9fff' or 0xff00<=ord(ch)<=0xffff)
print('files',len(j),'pairs',total,'chars',len(chars))
Path(r'D:\GALGUNVV\work\switch_story_cht_chars.txt').write_text(''.join(sorted(chars)),encoding='utf-8')
