from __future__ import annotations

import struct
import json
from pathlib import Path

from build_cht_font_test import find_remap, i32, parse_char_record


PACKAGE = Path(r"D:\GALGUNVV\work\full_cht_font_patch\Startup_LOC_INT.full_cht.upk")
FONT_OFFSET = 0x473C


def main() -> None:
    package = PACKAGE.read_bytes()
    font_size = json.loads(
        (PACKAGE.parent / "font_patch_report.json").read_text(encoding="utf-8")
    )["new_font_size"]
    font = package[FONT_OFFSET : FONT_OFFSET + font_size]
    count = i32(font, 0x1C)
    remap_offset, _ = find_remap(font, count)
    mapping = {}
    for entry in range(count):
        code, glyph = struct.unpack_from("<HH", font, remap_offset + entry * 4)
        mapping[code] = glyph

    for code in (0x76BF, 0x854A, 0x53F8):
        glyph = mapping.get(code)
        if glyph is None:
            raise RuntimeError(f"missing U+{code:04X}")
        record = parse_char_record(font, glyph)
        if record[2] <= 0 or record[3] <= 0 or record[4] >= 46:
            raise RuntimeError(f"invalid record for U+{code:04X}: {record}")
        print(f"U+{code:04X}: glyph={glyph}, record={record}")
    print(f"records={count}, mapped_codes={len(mapping)}")


if __name__ == "__main__":
    main()
