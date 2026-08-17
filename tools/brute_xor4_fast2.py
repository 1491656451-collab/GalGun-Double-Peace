from pathlib import Path
from collections import Counter
import itertools
b=Path(r'romfs\GG2Game\CookedNX\Coalesced_INT.bin').read_bytes()[:8192]
tops=[[x for x,n in Counter(b[i::4]).most_common(8)] for i in range(4)]
best=[]
for k in itertools.product(*tops):
 x=bytes(v^k[i%4] for i,v in enumerate(b))
 cnt=int.from_bytes(x[:4],'big'); s=(10 if 1<=cnt<=2000 else 0)
 s+=(2 if all(v>=0xf0 for v in x[4:8]) else 0)
 s+=sum(1 for i in range(5,len(x)-1,2) if x[i+1]==0)/100
 s+=sum(1 for i in range(0,len(x)-1,2) if 32<=x[i]<127 and x[i+1]==0)/100
 best.append((s,bytes(k),x[:32]))
for sc,k,x in sorted(best,reverse=True)[:20]:print(sc,k.hex(),x.hex(' '),''.join(chr(c) if 32<=c<127 else '.' for c in x))
