import json
from pathlib import Path
x=json.loads(Path(r'D:\GALGUNVV\work\fstrings_CHT.json').read_text(encoding='utf-8'))
for i in range(18,32): print(i, x[i]['off'], repr(x[i]['text']))
