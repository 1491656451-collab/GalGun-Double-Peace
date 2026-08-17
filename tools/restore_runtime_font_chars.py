from __future__ import annotations

import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

from PIL import Image

import sys

sys.path.insert(0, str(Path(__file__).parent))
import build_full_cht_font_patch as font_tools


ROOT = Path(r"D:\GALGUNVV")
GAME = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace")
PATCH = ROOT / "GG2CNPatch_Distribution_Final_20260809"
PACKAGE = GAME / "GG2Game" / "CookedPC" / "Startup_LOC_INT.upk"
ORIGINAL_PACKAGE = GAME / "GG2Game" / "CookedPC" / "Startup_LOC_INT.upk.original"
OUT_PACKAGE = ROOT / "work" / "runtime_font_restore" / "Startup_LOC_INT.upk"
REPORT = ROOT / "work" / "runtime_font_restore" / "font_restore_report.json"
FONT_OFFSET = 0x473C
PAGE_PREFIX_ROOT = ROOT / "work" / "current_startup_builder" / "raw_extract" / "Startup_LOC_INT" / "gg2_font" / "MessageFont"


def package_font(package: bytes) -> tuple[bytearray, int]:
    page_a = (PAGE_PREFIX_ROOT / "MessageFont_PageA.Texture2D").read_bytes()
    page_a_offset = package.find(page_a[:128])
    if page_a_offset <= FONT_OFFSET:
        raise RuntimeError("Could not locate MessageFont_PageA in current package")
    return bytearray(package[FONT_OFFSET:page_a_offset]), page_a_offset


def parse_font(font: bytes) -> tuple[int, int, list[tuple[int, int]]]:
    count = struct.unpack_from("<i", font, 0x1C)[0]
    remap, _ = font_tools.find_remap(font, count)
    pairs = [struct.unpack_from("<HH", font, remap + i * 4) for i in range(count)]
    return count, remap, pairs


def export_rows(package_path: Path) -> list[tuple[int, int, str]]:
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
        raise RuntimeError(f"Unexpected export count: {len(rows)}")
    return rows


def serial_positions(package: bytes, rows: list[tuple[int, int, str]]) -> list[int]:
    positions = []
    search_start = 0xD90
    previous = search_start - 1
    for old_offset, _, name in rows:
        needle = struct.pack("<I", old_offset)
        found = package.find(needle, search_start, 0x10000)
        while found >= 0 and found <= previous:
            found = package.find(needle, found + 1, 0x10000)
        if found < 0:
            raise RuntimeError(f"Could not locate serial offset for {name}")
        positions.append(found)
        previous = found
    return positions


def load_texture(raw: bytes) -> tuple[int, int, Image.Image]:
    width, height = font_tools.texture_size(raw)
    start = font_tools.texture_pixel_offset(raw)
    return width, height, Image.frombytes("L", (width, height), raw[start : start + width * height])


def read_localization_chars() -> set[int]:
    result: set[int] = set()
    root = PATCH / "GG2Game" / "Localization" / "INT"
    for path in root.glob("*.int"):
        text = path.read_bytes().decode("utf-16")
        for char in text:
            code = ord(char)
            if code > 0x7F and not (0x3040 <= code <= 0x30FF):
                result.add(code)
    return result


def main() -> None:
    current_package = PACKAGE.read_bytes()
    original_package = ORIGINAL_PACKAGE.read_bytes()
    current_font, current_page_a = package_font(current_package)
    original_font, _ = package_font(original_package)
    current_count, current_remap, current_pairs = parse_font(current_font)
    original_count, original_remap, original_pairs = parse_font(original_font)
    current_codes = {code for code, _ in current_pairs}
    original_by_code = {code: glyph for code, glyph in original_pairs}

    # Restore original punctuation and fullwidth numeric glyphs, plus any
    # non-Japanese characters present in the active localized files.
    requested = {
        code
        for code in (set(original_by_code) - current_codes)
        if not (0x3400 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF)
        and not (0x3040 <= code <= 0x30FF)
    }
    requested.update(read_localization_chars() - current_codes)
    requested = sorted(requested)
    if not requested:
        raise RuntimeError("No missing runtime characters found")

    # Reuse existing ASCII glyph records. This keeps the atlas unchanged and
    # avoids overwriting any of the newly added Traditional Chinese glyphs.
    current_by_code = {code: glyph for code, glyph in current_pairs}
    aliases = {
        0x3000: 0x20,
        0x3001: 0x2C,
        0x3002: 0x2E,
        0x300A: 0x28,
        0x300B: 0x29,
        0x2014: 0x2D,
        0x2018: 0x27,
        0x2019: 0x27,
        0x201C: 0x22,
        0x201D: 0x22,
        0x2026: 0x2E,
        0x266A: 0x2A,
        0x00B7: 0x2E,
        0x00E5: 0x61,
        0xFF01: 0x21,
        0xFF08: 0x28,
        0xFF09: 0x29,
        0xFF0C: 0x2C,
        0xFF1A: 0x3A,
        0xFF1B: 0x3B,
        0xFF1F: 0x3F,
    }
    for code in range(0xFF10, 0xFF1A):
        aliases[code] = 0x30 + code - 0xFF10
    for full, half in ((0xFF21, 0x41), (0xFF24, 0x44), (0xFF25, 0x45), (0xFF28, 0x48), (0xFF34, 0x54)):
        aliases[full] = half
    source_glyphs = {}
    for code in requested:
        source_code = aliases.get(code, code)
        if source_code not in current_by_code:
            raise RuntimeError(f"No safe source glyph for U+{code:04X}")
        source_glyphs[code] = current_by_code[source_code]

    records_end = 0x20 + current_count * 21
    marker_start = current_remap - 12
    gap = bytes(current_font[records_end:marker_start])
    old_remap = bytes(current_font[current_remap : current_remap + current_count * 4])
    new_count = current_count + len(requested)
    new_font = bytearray(current_font[:records_end])
    new_font.extend(b"\0" * (len(requested) * 21))
    new_font.extend(gap)
    new_font.extend(struct.pack("<iiI", 80, 0, new_count))
    new_font.extend(old_remap)
    new_font.extend(b"\0" * (len(requested) * 4))
    struct.pack_into("<i", new_font, 0x1C, new_count)
    new_remap = len(new_font) - new_count * 4

    assignments = []
    for offset, code in enumerate(requested):
        glyph_index = current_count + offset
        source_glyph = source_glyphs[code]
        source_record = font_tools.parse_char_record(current_font, source_glyph)
        x, y, width, height, page, vertical = source_record
        record_offset = 0x20 + glyph_index * 21
        struct.pack_into("<iiii", new_font, record_offset, x, y, width, height)
        new_font[record_offset + 16] = page
        struct.pack_into("<i", new_font, record_offset + 17, vertical)
        struct.pack_into("<I", new_font, new_remap + (current_count + offset) * 4, code | (glyph_index << 16))
        assignments.append({"codepoint": f"U+{code:04X}", "char": chr(code), "glyph_index": glyph_index, "source_codepoint": f"U+{next(key for key, value in current_by_code.items() if value == source_glyph):04X}", "page": page, "rect": [x, y, width, height]})

    new_package = bytearray(current_package[:FONT_OFFSET])
    new_package.extend(new_font)
    old_end = FONT_OFFSET + len(current_font)
    new_package.extend(current_package[old_end:])
    shift = len(new_font) - len(current_font)

    rows = export_rows(PACKAGE)
    positions = serial_positions(current_package, rows)
    for index, ((old_offset, _, _), position) in enumerate(zip(rows, positions)):
        if index == 2:
            struct.pack_into("<I", new_package, position - 4, len(new_font))
        elif old_offset >= old_end:
            struct.pack_into("<I", new_package, position, old_offset + shift)

    OUT_PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    OUT_PACKAGE.write_bytes(new_package)
    report = {
        "source_package": str(PACKAGE),
        "output_package": str(OUT_PACKAGE),
        "old_records": current_count,
        "new_records": new_count,
        "restored_characters": len(requested),
        "package_shift": shift,
        "assignments": assignments,
        "sha256": hashlib.sha256(new_package).hexdigest().upper(),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "assignments"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
