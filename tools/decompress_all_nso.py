from pathlib import Path
import struct,sys
# reuse function by import
sys.path.insert(0,'work')
from decompress_nso import nso_uncomp
for name in ['sdk','subsdk0','subsdk1','rtld']:
 src=Path('exefs')/name
 if not src.exists() or src.read_bytes()[:4]!=b'NSO0': continue
 try: nso_uncomp(str(src),str(Path('work/nso_all')/(name+'.uncompressed')))
 except Exception as e: print('FAIL',name,e)
