from __future__ import annotations

import json
import re
import struct
import subprocess
from pathlib import Path

from PIL import Image

import sys

sys.path.insert(0, r"D:\GALGUNVV\work")
import build_full_cht_font_patch as base


ROOT = Path(r"D:\GALGUNVV")
GAME = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace")
PACKAGE = GAME / "GG2Game" / "CookedPC" / "Startup_LOC_INT.upk.original"
OUT_PACKAGE = ROOT / "work" / "font_restore_missing" / "Startup_LOC_INT.restored.upk"
REPORT = ROOT / "work" / "font_restore_missing" / "font_restore_report.json"
OFFSETS = ROOT / "work" / "current_startup_builder" / "object_offsets.json"
BASE_REPORT = ROOT / "work" / "full_cht_font_patch" / "font_patch_report.json"
FONT_OFFSET = 0x473C


def cjk_codes() -> set[int]:
    result: set[int] = set()
    for path in (GAME / "GG2Game" / "Localization" / "INT").glob("GG2GirlDatas*.int"):
        raw = path.read_bytes()
        for encoding in ("utf-16", "utf-8", "cp932"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            continue
        result.update(
            ord(ch)
            for ch in text
            if 0x3400 <= ord(ch) <= 0x9FFF or 0xF900 <= ord(ch) <= 0xFAFF
        )
    return result


def read_export_rows(package_path: Path) -> list[tuple[int, int, str]]:
    result = subprocess.run(
        [r"D:\GALGUNVV\tools\umodel\umodel.exe", "-game=ue3", "-list", str(package_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    rows = []
    for line in result.stdout.splitlines() + result.stderr.splitlines():
        match = re.match(r"^\s*\d+\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+\S+\s+(\S+)", line)
        if match:
            rows.append((int(match.group(1), 16), int(match.group(2), 16), match.group(3)))
    if len(rows) != 54:
        raise RuntimeError(f"unexpected export count: {len(rows)}")
    return rows


def locate_serial_positions(package_data: bytes, rows: list[tuple[int, int, str]]) -> list[int]:
    positions = []
    search_start = 0xD90
    previous = search_start - 1
    for old_offset, _, name in rows:
        needle = struct.pack("<I", old_offset)
        candidates = []
        cursor = search_start
        while True:
            found = package_data.find(needle, cursor, 0x10000)
            if found < 0:
                break
            if found > previous:
                candidates.append(found)
            cursor = found + 1
        if not candidates:
            raise RuntimeError(f"could not locate export offset for {name} at {old_offset:X}")
        positions.append(candidates[0])
        previous = candidates[0]
    return positions


def main() -> None:
    package_data = PACKAGE.read_bytes()
    offsets = json.loads(OFFSETS.read_text(encoding="utf-8"))
    old_font_size = offsets["font"][1]
    existing_shift = 0
    font_data = bytearray(package_data[FONT_OFFSET : FONT_OFFSET + old_font_size])
    if len(font_data) != old_font_size:
        raise RuntimeError("current font object is truncated")

    char_count = base.i32(font_data, 0x1C)
    remap_offset, _ = base.find_remap(font_data, char_count)
    remap = [
        struct.unpack_from("<HH", font_data, remap_offset + index * 4)
        for index in range(char_count)
    ]
    mapped_codes = {code for code, _ in remap}
    missing_codes = sorted(cjk_codes() - mapped_codes)

    page_names = base.PAGE_NAMES
    textures: dict[int, tuple[bytearray, Image.Image, bytes]] = {}
    for index, page_name in enumerate(page_names):
        old_offset, size = offsets["pages"][page_name]
        page_offset = old_offset + existing_shift
        raw = bytearray(package_data[page_offset : page_offset + size])
        if len(raw) != size:
            raise RuntimeError(f"page {page_name} is truncated")
        width, height = base.texture_size(raw)
        pixel_offset = base.texture_pixel_offset(raw)
        pixels = bytes(raw[pixel_offset : pixel_offset + width * height])
        textures[index] = (raw, Image.frombytes("L", (width, height), pixels), bytes(raw))

    base.GLYPH_HEIGHT = 25
    rects = base.pack_rects(font_data, set(range(char_count)), textures)
    if len(rects) < len(missing_codes):
        raise RuntimeError(f"not enough unused atlas rectangles: {len(rects)} < {len(missing_codes)}")

    records_end = 0x20 + char_count * 21
    marker_start = remap_offset - 12
    gap = bytes(font_data[records_end:marker_start])
    old_remap = bytes(font_data[remap_offset : remap_offset + char_count * 4])
    new_count = char_count + len(missing_codes)
    new_font = bytearray(font_data[:records_end])
    new_font.extend(b"\0" * (len(missing_codes) * 21))
    new_font.extend(gap)
    new_font.extend(struct.pack("<iiI", 80, 0, new_count))
    new_font.extend(old_remap)
    new_font.extend(b"\0" * (len(missing_codes) * 4))
    struct.pack_into("<i", new_font, 0x1C, new_count)
    new_remap_offset = len(new_font) - new_count * 4

    font_path = base.choose_system_font()
    assignments = []
    for index, code in enumerate(missing_codes):
        glyph_index = char_count + index
        rect = rects[index]
        start_u, start_v, width, height, texture_index = rect
        struct.pack_into("<I", new_font, new_remap_offset + glyph_index * 4, code | (glyph_index << 16))
        record_offset = 0x20 + glyph_index * 21
        struct.pack_into("<iiii", new_font, record_offset, start_u, start_v, width, height)
        new_font[record_offset + 16] = texture_index
        base.put_i32(new_font, record_offset + 17, base.VERTICAL_OFFSET)
        base.draw_glyph(textures[texture_index][1], font_path, chr(code), rect[:4])
        assignments.append({"codepoint": f"U+{code:04X}", "char": chr(code), "glyph_index": glyph_index, "page": texture_index, "rect": list(rect[:4])})

    new_package = bytearray(package_data[:FONT_OFFSET])
    new_package.extend(new_font)
    new_package.extend(package_data[FONT_OFFSET + old_font_size :])
    font_delta = len(new_font) - old_font_size

    rows = read_export_rows(PACKAGE)
    serial_positions = locate_serial_positions(package_data, rows)
    for index, ((old_offset, _, _), offset_pos) in enumerate(zip(rows, serial_positions)):
        if index == 2:
            struct.pack_into("<I", new_package, offset_pos - 4, len(new_font))
        elif old_offset >= FONT_OFFSET + old_font_size:
            struct.pack_into("<I", new_package, offset_pos, old_offset + font_delta)

    for index, page_name in enumerate(page_names):
        old_offset, size = offsets["pages"][page_name]
        old_page_offset = old_offset + existing_shift
        new_page_offset = old_page_offset + font_delta
        raw, image, _ = textures[index]
        pixel_offset = base.texture_pixel_offset(raw)
        raw[pixel_offset : pixel_offset + image.width * image.height] = image.tobytes()
        new_package[new_page_offset : new_page_offset + size] = raw

    OUT_PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    OUT_PACKAGE.write_bytes(new_package)
    report = {
        "source_package": str(PACKAGE),
        "output_package": str(OUT_PACKAGE),
        "original_font_records": char_count,
        "new_font_records": new_count,
        "added_codepoints": len(missing_codes),
        "unused_atlas_rectangles": len(rects),
        "original_font_size": old_font_size,
        "new_font_size": len(new_font),
        "font_delta": font_delta,
        "package_size": len(new_package),
        "assignments": assignments,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "assignments"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
