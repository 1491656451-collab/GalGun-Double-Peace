from __future__ import annotations

import json
import re
import struct
import subprocess
from pathlib import Path

from PIL import Image

import sys

sys.path.insert(0, str(Path(__file__).parent))
import build_full_cht_font_patch as base
import build_cht_font_test as font_tools


ROOT = Path(r"D:\GALGUNVV")
GAME = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace")
PACKAGE = GAME / "GG2Game" / "CookedPC" / "Startup_LOC_INT.upk"
OUT_DIR = ROOT / "work" / "font_uniform_cht"
OUT_PACKAGE = OUT_DIR / "Startup_LOC_INT.uniform_cht.upk"
REPORT = OUT_DIR / "font_uniform_report.json"
OFFSETS = ROOT / "work" / "current_startup_builder" / "object_offsets.json"

FONT_OFFSET = 0x473C
ORIGINAL_FONT_OFFSET = 18236
ORIGINAL_FONT_SIZE = 52151
CURRENT_FONT_SIZE = 59301
CELL_WIDTH = 36
CELL_HEIGHT = 32


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


def decode_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-16", "utf-8", "cp932"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise RuntimeError(f"could not decode {path}")


def target_codes() -> set[int]:
    codes = {
        ord(ch)
        for ch in (ROOT / "work" / "switch_cht_texts" / "UsedWordsListCHT.txt").read_text(encoding="utf-8")
        if 0x3400 <= ord(ch) <= 0x9FFF
    }
    loc_root = GAME / "GG2Game" / "Localization" / "INT"
    for path in loc_root.glob("*.int"):
        text = decode_text(path)
        is_girl_data = path.name.lower().startswith("gg2girldatas")
        for line in text.splitlines():
            # [0] is the CHT branch in the PC localization files. Girl data
            # has no branch suffix, so all of its CJK characters are needed.
            if is_girl_data or "[0]" in line:
                codes.update(
                    ord(ch)
                    for ch in line
                    if 0x3400 <= ord(ch) <= 0x9FFF
                )
    return codes


def load_pages(package_data: bytes) -> tuple[dict[int, tuple[bytearray, Image.Image, Image.Image]], dict[str, list[int]]]:
    offsets = json.loads(OFFSETS.read_text(encoding="utf-8"))
    current_shift = CURRENT_FONT_SIZE - ORIGINAL_FONT_SIZE
    pages = {}
    for index, page_name in enumerate(font_tools.PAGE_NAMES):
        old_offset, size = offsets["pages"][page_name]
        page_offset = old_offset + current_shift if old_offset >= ORIGINAL_FONT_OFFSET + ORIGINAL_FONT_SIZE else old_offset
        raw = bytearray(package_data[page_offset : page_offset + size])
        if len(raw) != size:
            raise RuntimeError(f"truncated page {page_name}")
        width, height = font_tools.texture_size(raw)
        pixel_offset = font_tools.texture_pixel_offset(raw)
        pixels = bytes(raw[pixel_offset : pixel_offset + width * height])
        source = Image.frombytes("L", (width, height), pixels)
        pages[index] = (raw, source, Image.new("L", (width, height), 0))
    return pages, offsets


def slots(pages: dict[int, tuple[bytearray, Image.Image, Image.Image]]) -> list[tuple[int, int, int, int, int]]:
    result = []
    for index in range(len(font_tools.PAGE_NAMES)):
        image = pages[index][2]
        for y in range(0, image.height - CELL_HEIGHT + 1, CELL_HEIGHT):
            for x in range(0, image.width - CELL_WIDTH + 1, CELL_WIDTH):
                result.append((x, y, CELL_WIDTH, CELL_HEIGHT, index))
    return result


def copy_glyph(source: Image.Image, target: Image.Image, record: tuple[int, int, int, int, int, int], rect: tuple[int, int, int, int, int]) -> None:
    start_u, start_v, width, height, _, _ = record
    dest_u, dest_v, _, _, _ = rect
    if start_u < 0 or start_v < 0 or start_u + width > source.width or start_v + height > source.height:
        raise RuntimeError(f"invalid source glyph rectangle: {record}")
    target.paste(source.crop((start_u, start_v, start_u + width, start_v + height)), (dest_u, dest_v))


def build_font(package_data: bytes, old_font: bytes, remap: list[tuple[int, int]], missing: list[int], pages) -> tuple[bytes, dict]:
    old_count = len(remap)
    new_count = old_count + len(missing)
    all_slots = slots(pages)
    if len(all_slots) < new_count:
        raise RuntimeError(f"not enough 36x32 atlas slots: {len(all_slots)} < {new_count}")

    remap_offset, _ = font_tools.find_remap(old_font, old_count)
    records_end = 0x20 + old_count * 21
    marker_start = remap_offset - 12
    gap = bytes(old_font[records_end:marker_start])
    old_remap = bytes(old_font[remap_offset : remap_offset + old_count * 4])
    new_font = bytearray(old_font[:records_end])
    new_font.extend(b"\0" * (len(missing) * 21))
    new_font.extend(gap)
    new_font.extend(struct.pack("<iiI", 80, 0, new_count))
    new_font.extend(old_remap)
    new_font.extend(b"\0" * (len(missing) * 4))
    struct.pack_into("<i", new_font, 0x1C, new_count)
    new_remap_offset = len(new_font) - new_count * 4

    font_path = base.choose_system_font()
    assignments = []
    source_images = {index: page[1] for index, page in pages.items()}
    target_images = {index: page[2] for index, page in pages.items()}

    all_entries = remap + [(code, old_count + index) for index, code in enumerate(missing)]
    for entry_index, (code, old_glyph_index) in enumerate(all_entries):
        rect = all_slots[entry_index]
        dest_u, dest_v, _, _, texture_index = rect
        is_ascii = code < 0x80
        if old_glyph_index < old_count:
            old_record = font_tools.parse_char_record(old_font, old_glyph_index)
            if is_ascii and old_record[2] <= CELL_WIDTH and old_record[3] <= CELL_HEIGHT:
                copy_glyph(source_images[old_record[4]], target_images[texture_index], old_record, rect)
                width = old_record[2]
                height = old_record[3]
                vertical_offset = old_record[5]
            else:
                width = CELL_WIDTH if not is_ascii else min(CELL_WIDTH, max(1, old_record[2]))
                height = CELL_HEIGHT if not is_ascii else min(CELL_HEIGHT, max(1, old_record[3]))
                base.draw_glyph(target_images[texture_index], font_path, chr(code), (dest_u, dest_v, width, height))
                vertical_offset = 7 if not is_ascii else old_record[5]
        else:
            width = CELL_WIDTH
            height = CELL_HEIGHT
            base.draw_glyph(target_images[texture_index], font_path, chr(code), (dest_u, dest_v, width, height))
            vertical_offset = 7

        record_offset = 0x20 + old_glyph_index * 21
        struct.pack_into("<iiii", new_font, record_offset, dest_u, dest_v, width, height)
        new_font[record_offset + 16] = texture_index
        font_tools.put_i32(new_font, record_offset + 17, vertical_offset)
        remap_value = code | (old_glyph_index << 16)
        struct.pack_into("<I", new_font, new_remap_offset + entry_index * 4, remap_value)
        assignments.append({"codepoint": f"U+{code:04X}", "glyph_index": old_glyph_index, "page": texture_index, "rect": [dest_u, dest_v, width, height]})

    old_end = FONT_OFFSET + len(old_font)
    shift = len(new_font) - len(old_font)
    output = bytearray(package_data[:FONT_OFFSET])
    output.extend(new_font)
    output.extend(package_data[old_end:])

    rows = read_export_rows(PACKAGE)
    serial_positions = locate_serial_positions(package_data, rows)
    for index, ((old_offset, _, _), offset_pos) in enumerate(zip(rows, serial_positions)):
        if index == 2:
            struct.pack_into("<I", output, offset_pos - 4, len(new_font))
        elif old_offset >= old_end:
            struct.pack_into("<I", output, offset_pos, old_offset + shift)

    for index, page_name in enumerate(font_tools.PAGE_NAMES):
        raw, _, image = pages[index]
        pixel_offset = font_tools.texture_pixel_offset(raw)
        width, height = image.size
        raw[pixel_offset : pixel_offset + width * height] = image.tobytes()
        old_offset, size = json.loads(OFFSETS.read_text(encoding="utf-8"))["pages"][page_name]
        current_offset = old_offset + (CURRENT_FONT_SIZE - ORIGINAL_FONT_SIZE)
        new_offset = current_offset + shift if current_offset >= old_end else current_offset
        output[new_offset : new_offset + size] = raw

    report = {
        "source_package": str(PACKAGE),
        "output_package": str(OUT_PACKAGE),
        "old_records": old_count,
        "new_records": new_count,
        "added_codes": len(missing),
        "cell_width": CELL_WIDTH,
        "cell_height": CELL_HEIGHT,
        "atlas_slots": len(all_slots),
        "font_size_before": len(old_font),
        "font_size_after": len(new_font),
        "package_shift": shift,
        "assignments": assignments,
    }
    return bytes(output), report


def main() -> None:
    package_data = PACKAGE.read_bytes()
    old_font = package_data[FONT_OFFSET : FONT_OFFSET + CURRENT_FONT_SIZE]
    if len(old_font) != CURRENT_FONT_SIZE:
        raise RuntimeError("current MessageFont object is truncated")
    old_count = font_tools.i32(old_font, 0x1C)
    remap_offset, _ = font_tools.find_remap(old_font, old_count)
    remap = [struct.unpack_from("<HH", old_font, remap_offset + index * 4) for index in range(old_count)]
    mapped_codes = {code for code, _ in remap}
    missing = sorted(target_codes() - mapped_codes)
    pages, _ = load_pages(package_data)
    output, report = build_font(package_data, old_font, remap, missing, pages)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PACKAGE.write_bytes(output)
    report["target_codes"] = len(target_codes())
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "assignments"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
