from __future__ import annotations

import json
import struct
import re
import subprocess
from pathlib import Path

from PIL import Image

import sys
sys.path.insert(0, r"D:\GALGUNVV\work")
from build_cht_font_test import (
    PAGE_NAMES,
    choose_system_font,
    draw_glyph,
    find_remap,
    i32,
    parse_char_record,
    put_i32,
    texture_pixel_offset,
    texture_size,
)

ROOT = Path(r"D:\GALGUNVV")
PACKAGE = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\CookedPC\Startup_LOC_INT.upk.original")
RAW_ROOT = ROOT / "work" / "current_startup_builder" / "raw_extract" / "Startup_LOC_INT"
FONT_OBJECT = RAW_ROOT / "gg2_font" / "MessageFont.Font"
TEXTURE_ROOT = RAW_ROOT / "gg2_font" / "MessageFont"
WORD_LIST = ROOT / "work" / "switch_cht_texts" / "UsedWordsListCHT.txt"
NORMALIZED_UI_REPORT = ROOT / "work" / "full_cht_font_patch" / "font_patch_normalized_ui_report.json"
OUT_PACKAGE = ROOT / "work" / "full_cht_font_patch" / "Startup_LOC_INT.full_cht.upk"
REPORT = ROOT / "work" / "full_cht_font_patch" / "font_patch_report.json"

GLYPH_WIDTH = 36
# The combined UI/name set needs a few more atlas cells than the original
# 36x34 packing leaves available.  A 32px cell still fits the existing font
# metrics and provides enough room without adding Texture2D exports.
GLYPH_HEIGHT = 32
VERTICAL_OFFSET = 7


def preserve_source_code(code: int) -> bool:
    return 0x20 <= code < 0x7F or 0xFF10 <= code <= 0xFF19


def load_font_and_remap() -> tuple[bytearray, int, int, list[tuple[int, int]]]:
    font_data = bytearray(FONT_OBJECT.read_bytes())
    char_count = i32(font_data, 0x1C)
    remap_offset, _ = find_remap(font_data, char_count)
    remap = []
    for entry in range(char_count):
        off = remap_offset + entry * 4
        code = struct.unpack_from("<H", font_data, off)[0]
        glyph_index = struct.unpack_from("<H", font_data, off + 2)[0]
        remap.append((code, glyph_index))
    return font_data, char_count, remap_offset, remap


def load_textures() -> dict[int, tuple[bytearray, Image.Image, bytes]]:
    textures: dict[int, tuple[bytearray, Image.Image, bytes]] = {}
    for index, page_name in enumerate(PAGE_NAMES):
        path = TEXTURE_ROOT / f"{page_name}.Texture2D"
        raw = bytearray(path.read_bytes())
        width, height = texture_size(raw)
        pixels = bytes(raw[texture_pixel_offset(raw) : texture_pixel_offset(raw) + width * height])
        textures[index] = (raw, Image.frombytes("L", (width, height), pixels), bytes(raw))
    return textures


def pack_rects(font_data: bytes, protected_indices: set[int], textures) -> list[tuple[int, int, int, int, int]]:
    dimensions: dict[int, tuple[int, int]] = {}
    occupancy: dict[int, bytearray] = {}
    for index, (raw, _, _) in textures.items():
        width, height = texture_size(raw)
        dimensions[index] = (width, height)
        occupancy[index] = bytearray(width * height)

    def mark(texture_index: int, x: int, y: int, width: int, height: int) -> None:
        page_width, page_height = dimensions[texture_index]
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(page_width, x + width), min(page_height, y + height)
        if x1 <= x0 or y1 <= y0:
            return
        row = b"\x01" * (x1 - x0)
        for yy in range(y0, y1):
            off = yy * page_width + x0
            occupancy[texture_index][off : off + len(row)] = row

    for glyph_index in protected_indices:
        start_u, start_v, width, height, texture_index, _ = parse_char_record(font_data, glyph_index)
        if 0 <= texture_index < len(PAGE_NAMES) and width > 0 and height > 0:
            mark(texture_index, start_u, start_v, width, height)

    def free(texture_index: int, x: int, y: int) -> bool:
        page_width, _ = dimensions[texture_index]
        page = occupancy[texture_index]
        for yy in range(y, y + GLYPH_HEIGHT):
            off = yy * page_width + x
            if any(page[off : off + GLYPH_WIDTH]):
                return False
        return True

    rects = []
    for texture_index in range(len(PAGE_NAMES)):
        width, height = dimensions[texture_index]
        for y in range(0, height - GLYPH_HEIGHT + 1):
            x = 0
            while x <= width - GLYPH_WIDTH:
                if free(texture_index, x, y):
                    rect = (x, y, GLYPH_WIDTH, GLYPH_HEIGHT, texture_index)
                    rects.append(rect)
                    mark(texture_index, x, y, GLYPH_WIDTH, GLYPH_HEIGHT)
                    x += GLYPH_WIDTH
                else:
                    x += 1
    return rects


def extend_font_object(font_data: bytearray, char_count: int, remap_offset: int, remap: list[tuple[int, int]], assignments: list[tuple[str, int, tuple[int, int, int, int, int]]]) -> bytes:
    old_marker = remap_offset - 12
    records_end = 0x20 + char_count * 21
    gap = bytes(font_data[records_end:old_marker])
    old_remap = bytes(font_data[remap_offset : remap_offset + char_count * 4])
    new_count = char_count + sum(1 for ch, _, _ in assignments if _ >= char_count)
    # The caller has already appended exactly the required new record count.
    new_records_count = new_count - char_count

    prefix = bytearray(font_data[:records_end])
    prefix.extend(b"\x00" * (new_records_count * 21))
    prefix.extend(gap)
    prefix.extend(struct.pack("<iiI", 80, 0, new_count))
    prefix.extend(old_remap)
    prefix.extend(b"\x00" * (new_count - char_count) * 4)
    struct.pack_into("<i", prefix, 0x1C, new_count)

    # Fill remap entries and glyph records.
    new_remap_offset = len(prefix) - new_count * 4
    for code, glyph_index, rect in assignments:
        start_u, start_v, width, height, texture_index = rect
        record_offset = 0x20 + glyph_index * 21
        struct.pack_into("<iiii", prefix, record_offset, start_u, start_v, width, height)
        prefix[record_offset + 16] = texture_index
        put_i32(prefix, record_offset + 17, VERTICAL_OFFSET)

    # Existing entries are updated by the caller through assignment order.
    for entry_index, (code, glyph_index, _) in enumerate(assignments):
        if entry_index < char_count:
            struct.pack_into("<I", prefix, new_remap_offset + entry_index * 4, code | (glyph_index << 16))
        else:
            struct.pack_into("<I", prefix, new_remap_offset + entry_index * 4, code | (glyph_index << 16))
    return bytes(prefix)


def main() -> None:
    font_data, char_count, remap_offset, remap = load_font_and_remap()
    desired_chars = [ch for ch in WORD_LIST.read_text(encoding="utf-8").strip() if ord(ch) >= 0x80 and not ch.isspace()]
    # Keep the characters added by the previously validated UI build.  The
    # report is intentionally read by codepoint so it remains valid even when
    # a console uses a legacy encoding for the glyph preview text.
    if NORMALIZED_UI_REPORT.exists():
        report_text = NORMALIZED_UI_REPORT.read_text(encoding="utf-8")
        for codepoint in dict.fromkeys(re.findall(r'"codepoint"\s*:\s*"U\+([0-9A-Fa-f]{4,6})"', report_text)):
            desired_chars.append(chr(int(codepoint, 16)))
    live_int_root = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\Localization\INT")
    for name_file in ("GG2GirlDatas.int", "GG2GirlDatas_Eng.int"):
        text = (live_int_root / name_file).read_text(encoding="utf-16")
        desired_chars.extend(ch for ch in text if ord(ch) >= 0x80 and not ch.isspace())
    desired_chars = list(dict.fromkeys(desired_chars))
    code_to_entry = {code: index for index, (code, _) in enumerate(remap)}
    desired_codes = {ord(ch) for ch in desired_chars}
    missing_chars = [ch for ch in desired_chars if ord(ch) not in code_to_entry]

    protected_indices = {
        glyph_index
        for code, glyph_index in remap
        if preserve_source_code(code) or code in desired_codes
    }
    available_entries = [
        index for index, (code, _) in enumerate(remap)
        if not preserve_source_code(code) and code not in desired_codes
    ]
    available_indices = [index for index in range(char_count) if index not in protected_indices]
    new_records_needed = max(0, len(missing_chars) - len(available_indices))
    next_new_index = char_count
    total_new_count = char_count + new_records_needed
    if len(available_entries) + new_records_needed < len(missing_chars):
        raise RuntimeError("Not enough remap entries even after extending Font records")

    textures = load_textures()
    rects = pack_rects(font_data, protected_indices, textures)
    if len(rects) < len(missing_chars):
        raise RuntimeError(f"Not enough atlas rectangles: {len(rects)} < {len(missing_chars)}")

    # Construct the extended object layout first.
    old_marker = remap_offset - 12
    records_end = 0x20 + char_count * 21
    gap = bytes(font_data[records_end:old_marker])
    old_remap = bytes(font_data[remap_offset : remap_offset + char_count * 4])
    new_font = bytearray(font_data[:records_end])
    new_font.extend(b"\x00" * (new_records_needed * 21))
    new_font.extend(gap)
    new_font.extend(struct.pack("<iiI", 80, 0, total_new_count))
    new_font.extend(old_remap)
    new_font.extend(b"\x00" * ((total_new_count - char_count) * 4))
    struct.pack_into("<i", new_font, 0x1C, total_new_count)
    new_remap_offset = len(new_font) - total_new_count * 4

    assignments = []
    assignment_report = []
    for index, ch in enumerate(missing_chars):
        if index < len(available_entries):
            remap_entry = available_entries[index]
            glyph_index = available_indices[index]
        else:
            remap_entry = char_count + (index - len(available_entries))
            glyph_index = next_new_index
            next_new_index += 1
        rect = rects[index]
        code = ord(ch)
        struct.pack_into("<I", new_font, new_remap_offset + remap_entry * 4, code | (glyph_index << 16))
        record_offset = 0x20 + glyph_index * 21
        start_u, start_v, width, height, texture_index = rect
        struct.pack_into("<iiii", new_font, record_offset, start_u, start_v, width, height)
        new_font[record_offset + 16] = texture_index
        put_i32(new_font, record_offset + 17, VERTICAL_OFFSET)
        draw_glyph(textures[texture_index][1], choose_system_font(), ch, rect[:4])
        assignments.append((ch, glyph_index, rect))
        assignment_report.append({"char": ch, "codepoint": f"U+{code:04X}", "glyph_index": glyph_index, "remap_entry": remap_entry, "page": texture_index, "rect": list(rect[:4])})

    package_data = bytearray(PACKAGE.read_bytes())
    old_size = len(font_data)
    font_offset = package_data.find(bytes(font_data))
    if font_offset < 0:
        font_offset = 0x473C
    if package_data[font_offset : font_offset + old_size] != bytes(font_data):
        raise RuntimeError("Could not locate the current MessageFont object")

    # Locate every export's serial-offset field from UModel's object list.
    # UE3 uses a few different export-record layouts for Package objects, so a
    # fixed stride is not safe here; the serial offset itself is unique in the
    # export table and can be located directly.
    listing = subprocess.run(
        [r"D:\GALGUNVV\tools\umodel\umodel.exe", "-game=ue3", "-list", str(PACKAGE)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
    )
    listing_text = listing.stdout + "\n" + listing.stderr
    export_rows = []
    for line in listing_text.splitlines():
        match = re.match(r"^\s*\d+\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+\S+\s+(\S+)", line)
        if match:
            export_rows.append((int(match.group(1), 16), int(match.group(2), 16), match.group(3)))
    if len(export_rows) != 54:
        raise RuntimeError(f"Unexpected export count: {len(export_rows)}")
    serial_positions = []
    search_start = 0xD90
    previous = search_start - 1
    for old_export_offset, old_export_size, name in export_rows:
        needle = struct.pack("<I", old_export_offset)
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
            raise RuntimeError(f"Could not locate export offset for {name} at {old_export_offset:X}")
        chosen = candidates[0]
        serial_positions.append(chosen)
        previous = chosen
    font_export_index = 2
    serial_offset_pos = serial_positions[font_export_index]
    serial_size_pos = serial_offset_pos - 4
    if struct.unpack_from("<I", package_data, serial_size_pos)[0] != old_size:
        raise RuntimeError("Unexpected MessageFont serial size field")
    if struct.unpack_from("<I", package_data, serial_offset_pos)[0] != font_offset:
        raise RuntimeError("Unexpected MessageFont serial offset field")

    old_end = font_offset + old_size
    shift = len(new_font) - old_size
    package_data = package_data[:font_offset] + new_font + package_data[old_end:]

    for export_index, ((old_export_offset, old_export_size, name), offset_pos) in enumerate(zip(export_rows, serial_positions)):
        size_pos = offset_pos - 4
        if export_index == font_export_index:
            struct.pack_into("<I", package_data, size_pos, len(new_font))
        if export_index != font_export_index and old_export_offset >= old_end:
            struct.pack_into("<I", package_data, offset_pos, old_export_offset + shift)

    # Write updated atlas pages back into their original Texture2D blobs. Their
    # serial offsets were shifted together with the rest of the package.
    offsets = json.loads((ROOT / "work" / "current_startup_builder" / "object_offsets.json").read_text(encoding="utf-8"))["pages"]
    for index, page_name in enumerate(PAGE_NAMES):
        raw, image, original = textures[index]
        pixel_offset = texture_pixel_offset(raw)
        raw[pixel_offset : pixel_offset + image.width * image.height] = image.tobytes()
        old_page_offset, size = offsets[page_name]
        page_offset = old_page_offset + shift if old_page_offset >= old_end else old_page_offset
        if len(raw) != size:
            raise RuntimeError((page_name, len(raw), size))
        package_data[page_offset : page_offset + size] = raw

    OUT_PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    OUT_PACKAGE.write_bytes(package_data)
    report = {
        "source_package": str(PACKAGE),
        "output_package": str(OUT_PACKAGE),
        "original_font_records": char_count,
        "new_font_records": total_new_count,
        "used_characters": len(desired_chars),
        "already_mapped": len(desired_chars) - len(missing_chars),
        "new_characters": len(missing_chars),
        "reused_old_records": min(len(missing_chars), len(available_indices)),
        "appended_records": new_records_needed,
        "atlas_rectangles": len(rects),
        "font_object_offset": font_offset,
        "package_shift": shift,
        "original_font_size": len(font_data),
        "new_font_size": len(new_font),
        "export_size_field": serial_size_pos,
        "assignments": assignment_report,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k != "assignments"}, ensure_ascii=False))


if __name__ == "__main__":
    main()


