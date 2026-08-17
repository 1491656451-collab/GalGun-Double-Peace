from pathlib import Path
import json, struct, subprocess, tempfile, re, sys

ROOT = Path(r'D:\GALGUNVV')
SRC = ROOT / 'romfs' / 'GG2Game' / 'CookedNX'
IDX = ROOT / 'work' / 'cht_map_index.json'
DEC = Path(r'D:\虚幻解包\GALGUN汉化源文件\GG2CNPatch\tools\decompress\decompress.exe')
OUT = ROOT / 'work' / 'switch_cht_texts' / 'all_switch_cht_texts_clean.json'
REPORT = ROOT / 'work' / 'switch_cht_texts' / 'clean_extract_report.json'


def plausible(s: str) -> bool:
    if not s or len(s) > 400:
        return False
    # Actual UE text is printable UTF-16 text; binary false positives contain NUL/control/private-use chars.
    if any(ord(c) < 0x20 for c in s):
        return False
    if any(0xD800 <= ord(c) <= 0xDFFF for c in s):
        return False
    if any(0xE000 <= ord(c) <= 0xF8FF for c in s):
        return False
    return True


def extract_strings(blob: bytes):
    candidates = []
    for off in range(0, len(blob) - 4):
        n = struct.unpack_from('<i', blob, off)[0]
        if n >= 0 or n < -10000:
            continue
        count = -n
        end = off + 4 + count * 2
        if end > len(blob):
            continue
        raw = blob[off + 4:end]
        if raw[-2:] != b'\0\0':
            continue
        try:
            s = raw[:-2].decode('utf-16le')
        except UnicodeDecodeError:
            continue
        if plausible(s):
            candidates.append((off, s))
    seen = set()
    out = []
    for off, s in candidates:
        if off not in seen:
            seen.add(off)
            out.append((off, s))
    return out


def main():
    idx = json.loads(IDX.read_text(encoding='utf-8'))
    result = {}
    report = []
    with tempfile.TemporaryDirectory(prefix='gg2_cht_', dir=ROOT / 'work') as td:
        tmp = Path(td)
        for num, name in enumerate(sorted(idx), 1):
            info = idx[name]
            src = SRC / name
            out_file = tmp / name
            p = subprocess.run([str(DEC), '-game=ue3', f'-out={tmp}', str(src)], capture_output=True, text=True, timeout=180)
            if p.returncode != 0 or not out_file.exists():
                report.append({'file': name, 'status': 'decompress_failed', 'returncode': p.returncode, 'stderr': p.stderr[-500:]})
                continue
            all_bytes = out_file.read_bytes()
            blob = all_bytes[info['offset']:info['offset'] + info['size']]
            strings = extract_strings(blob)
            if len(strings) % 2:
                report.append({'file': name, 'status': 'odd_string_count', 'count': len(strings), 'strings': [s for _, s in strings]})
            pairs = [{'name': strings[i + 1][1] if i + 1 < len(strings) else '', 'text': strings[i][1]} for i in range(0, len(strings), 2)]
            result[name] = {'object': info['object'], 'strings': [s for _, s in strings], 'pairs': pairs, 'string_count': len(strings)}
            report.append({'file': name, 'status': 'ok', 'string_count': len(strings), 'pair_count': len(pairs)})
            if num % 25 == 0:
                print(f'processed {num}/{len(idx)}', flush=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('done', len(result), 'files', 'pairs', sum(len(v['pairs']) for v in result.values()))

if __name__ == '__main__':
    main()

