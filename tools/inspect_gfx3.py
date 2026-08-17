from __future__ import annotations

import pathlib
import struct
import sys


def read_ub(data: bytes, pos: int, n: int) -> tuple[int, int]:
    value = 0
    for _ in range(n):
        value = (value << 1) | ((data[pos // 8] >> (7 - (pos % 8))) & 1)
        pos += 1
    return value, pos


def read_rect_end(data: bytes, bit_pos: int) -> int:
    nbits, bit_pos = read_ub(data, bit_pos, 5)
    for _ in range(4):
        _, bit_pos = read_ub(data, bit_pos, nbits)
    return (bit_pos + 7) // 8


def ascii_runs(data: bytes, minimum: int = 3):
    start = None
    for i, value in enumerate(data + b"\0"):
        printable = 32 <= value < 127
        if printable and start is None:
            start = i
        elif not printable and start is not None:
            if i - start >= minimum:
                yield start, data[start:i].decode("ascii")
            start = None


def inspect(path: pathlib.Path):
    data = path.read_bytes()
    print(f"{path}: {len(data)} bytes, header={data[:8]!r}")
    pos = read_rect_end(data, 8 * 8)
    pos += 4
    print(f"tag stream starts at 0x{pos:X}")
    terms = ("story", "continue", "collection", "score", "quit", "gallery", "option", "dressing", "data")
    index = 0
    while pos + 2 <= len(data):
        record = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        tag_code = record >> 6
        length = record & 0x3F
        if length == 0x3F:
            if pos + 4 > len(data):
                break
            length = struct.unpack_from("<I", data, pos)[0]
            pos += 4
        body_start = pos
        body_end = pos + length
        if body_end > len(data):
            print(f"tag {index}: code={tag_code} truncated at 0x{body_start:X}, len={length}")
            break
        hits = [(off, text) for off, text in ascii_runs(data[body_start:body_end], 4)
                if any(term in text.lower() for term in terms)]
        if hits:
            print(f"tag {index}: code={tag_code} body=0x{body_start:X} len=0x{length:X}")
            for off, text in hits:
                print(f"  0x{body_start + off:X}: {text!r}")
        pos = body_end
        index += 1
        if tag_code == 0:
            break


for item in sys.argv[1:]:
    inspect(pathlib.Path(item))
