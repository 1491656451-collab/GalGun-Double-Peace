from pathlib import Path
from collections import Counter
import itertools,struct
b=Path(r'romfs\GG2Game\CookedNX\Coalesced_INT.bin').read_bytes()
tops=[ [x for x,n in Counter(b[i::4]).most_common(30)] for i in range(4)]
def score(k):
 x=bytes(v^k[i%4] for i,v in enumerate(b[:200000]))
 cnt=int.from_bytes(x[:4],'big'); s=0
 if 1<=cnt<=2000:s+=10
 # inverted UTF16 length then likely UTF16LE
 if x[4:8][0]>=0xf0 and x[4:8][1]>=0xf0:s+=2
 # count zero high bytes in first 100k
 s+=sum(1 for i in range(5,len(x)-1,2) if x[i+1]==0)/1000
 # printable / UTF16
 s+=sum(1 for i in range(0,len(x)-1,2) if 32<=x[i]<127 and x[i+1]==0)/1000
 return s,x[:32]
best=[]
for k in itertools.product(*tops):
 sc,x=score(bytes(k)); best.append((sc,bytes(k),x))
for sc,k,x in sorted(best,reverse=True)[:20]: print(sc,k.hex(),x.hex(' '),''.join(chr(c) if 32<=c<127 else '.' for c in x))
