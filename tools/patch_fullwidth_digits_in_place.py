from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

from PIL import Image

import sys

sys.path.insert(0, str(Path(__file__).parent))
from build_cht_font_test import find_remap, parse_char_record


ROOT = Path(r"D:\GALGUNVV")
GOOD_PACKAGE = ROOT / "work" / "font_add_active_normal_20260809" / "Startup_LOC_INT.active_normal.upk"
ORIGINAL_PACKAGE = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\CookedPC\Startup_LOC_INT.upk.original")
OUT_PACKAGE = ROOT / "work" / "runtime_font_restore" / "Startup_LOC_INT.digits_in_place.upk"
REPORT = ROOT / "work" / "runtime_font_restore" / "digits_in_place_report.json"
FONT_OFFSET = 0x473C
OFFSETS = ROOT / "work" / "current_startup_builder" / "object_offsets.json"
ORIGINAL_DIGIT_PAGE = ROOT / "work" / "original_digit_export" / "original" / "Texture2D" / "MessageFont_PageBS.png"
LOC_ROOT = ROOT / "GG2CNPatch_Distribution_Final_20260809" / "GG2Game" / "Localization" / "INT"

ORIGINAL_FONT_SIZE = 52151

# These are Japanese-only source glyph codes in the current CHT package. The
# check below refuses to use a victim if it appears in any shipped text file.
VICTIMS = [0x4E21, 0x4ED5, 0x4F1D, 0x51B4, 0x53E9, 0x5840, 0x59C9, 0x5BFE, 0x6226, 0x6451]

# Original fullwidth digit records in the unmodified font. They live on
# MessageFont_PageBS (texture index 44) and are copied into the replacement
# slots below without enlarging the font object or atlas textures.
ORIGINAL_DIGITS = [
    (77, 83, 28, 31, 44, 8),
    (106, 83, 13, 30, 44, 9),
    (120, 83, 26, 30, 44, 8),
    (147, 83, 26, 31, 44, 8),
    (174, 83, 30, 30, 44, 9),
    (205, 83, 26, 30, 44, 9),
    (1, 122, 26, 31, 44, 8),
    (28, 122, 26, 30, 44, 9),
    (55, 122, 28, 31, 44, 8),
    (84, 122, 26, 31, 44, 8),
]

PAGE_NAMES = (
    ["MessageFont_PageA", "MessageFont_PageB"]
    + [f"MessageFont_Page{chr(c)}" for c in range(ord("C"), ord("Z") + 1)]
    + [f"MessageFont_PageB{chr(c)}" for c in range(ord("A"), ord("T") + 1)]
)


def texture_pixel_offset(texture_data: bytes) -> int:
    return 0x172


def texture_size(texture_data: bytes) -> tuple[int, int]:
    return struct.unpack_from("<ii", texture_data, 0x1C)[0], struct.unpack_from("<ii", texture_data, 0x38)[0]


def rects_overlap(a: tuple[int, int, int, int, int], b: tuple[int, int, int, int, int]) -> bool:
    ax, ay, aw, ah, ap = a
    bx, by, bw, bh, bp = b
    return ap == bp and ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def main() -> None:
    if not ORIGINAL_DIGIT_PAGE.exists():
        raise RuntimeError("Export the original MessageFont_PageBS texture first.")

    package = bytearray(GOOD_PACKAGE.read_bytes())
    if not ORIGINAL_PACKAGE.exists() or len(package) <= len(ORIGINAL_PACKAGE.read_bytes()):
        raise RuntimeError("Source package size does not contain the expected expanded font")
    font_delta = len(package) - len(ORIGINAL_PACKAGE.read_bytes())
    current_font_size = ORIGINAL_FONT_SIZE + font_delta
    font_end = FONT_OFFSET + current_font_size
    font = bytearray(package[FONT_OFFSET:font_end])
    if len(font) != current_font_size:
        raise RuntimeError("Could not locate the expanded MessageFont object")
    count = struct.unpack_from("<i", font, 0x1C)[0]
    remap, _ = find_remap(font, count)
    pairs = [struct.unpack_from("<HH", font, remap + index * 4) for index in range(count)]
    by_code = {code: (index, glyph) for index, (code, glyph) in enumerate(pairs)}

    used_codes: set[int] = set()
    for path in LOC_ROOT.glob("*.int"):
        used_codes.update(ord(char) for char in path.read_bytes().decode("utf-16"))
    unsafe = [code for code in VICTIMS if code not in by_code or code in used_codes]
    if unsafe:
        raise RuntimeError(f"Victim codes are unavailable or used: {unsafe}")

    victim_glyphs = []
    for victim in VICTIMS:
        if victim not in by_code:
            raise RuntimeError(f"Victim code U+{victim:04X} is not mapped in the source package")
        entry, glyph = by_code[victim]
        victim_glyphs.append(glyph)

    if len(set(victim_glyphs)) != len(victim_glyphs):
        raise RuntimeError("Victim glyph records are not unique")

    # Confirm the replacement cells are not shared with any other glyph
    # record before clearing their old CJK pixels.
    for glyph in victim_glyphs:
        target = parse_char_record(font, glyph)
        target_rect = target[:4] + (target[4],)
        for other in range(count):
            if other == glyph:
                continue
            record = parse_char_record(font, other)
            other_rect = record[:4] + (record[4],)
            if rects_overlap(target_rect, other_rect):
                raise RuntimeError(f"Target glyph {glyph} overlaps glyph {other}")

    source = Image.open(ORIGINAL_DIGIT_PAGE).convert("L")
    source_width, source_height = source.size
    if source_width != 256 or source_height < 153:
        raise RuntimeError(f"Unexpected original digit page size: {source.size}")

    # Load the current atlas pages from the package. The raw extracted files
    # provide the UE3 object bytes and the pixel payload offset.
    offsets = json.loads(OFFSETS.read_text(encoding="utf-8"))["pages"]
    page_objects: dict[int, tuple[int, bytearray, Image.Image]] = {}
    for texture_index, page_name in enumerate(PAGE_NAMES):
        original_offset, expected_size = offsets[page_name]
        location = original_offset + font_delta
        raw = bytearray(package[location : location + expected_size])
        if len(raw) != expected_size:
            raise RuntimeError(f"Could not locate {page_name} in source package")
        width, height = texture_size(raw)
        pixel_offset = texture_pixel_offset(raw)
        pixels = bytes(package[location + pixel_offset : location + pixel_offset + width * height])
        if len(pixels) != width * height:
            raise RuntimeError(f"Truncated pixel payload for {page_name}")
        page_objects[texture_index] = (
            location,
            bytearray(package[location : location + len(raw)]),
            Image.frombytes("L", (width, height), pixels),
        )

    assignments = []
    for digit, victim in enumerate(VICTIMS):
        entry_index = by_code[victim][0]
        fullwidth_code = 0xFF10 + digit
        glyph_index = victim_glyphs[digit]
        old_u, old_v, old_width, old_height, target_page, _ = parse_char_record(font, glyph_index)
        src_u, src_v, src_width, src_height, src_page, src_vertical_offset = ORIGINAL_DIGITS[digit]
        if src_page != 44:
            raise RuntimeError("Unexpected source digit texture index")
        if src_u + src_width > source_width or src_v + src_height > source_height:
            raise RuntimeError(f"Original digit {digit} crop is outside PageBS")
        target_cell_width, target_cell_height = 36, 32
        if src_width > target_cell_width or src_height > target_cell_height:
            raise RuntimeError(f"Original digit {digit} does not fit replacement cell")
        dst_u = old_u + (target_cell_width - src_width) // 2
        dst_v = old_v + (target_cell_height - src_height) // 2

        _, target_raw, target_image = page_objects[target_page]
        target_image.paste(0, (old_u, old_v, old_u + target_cell_width, old_v + target_cell_height))
        target_image.paste(source.crop((src_u, src_v, src_u + src_width, src_v + src_height)), (dst_u, dst_v))

        record_offset = 0x20 + glyph_index * 21
        struct.pack_into("<iiii", font, record_offset, dst_u, dst_v, src_width, src_height)
        font[record_offset + 16] = target_page
        struct.pack_into("<i", font, record_offset + 17, src_vertical_offset)
        struct.pack_into("<I", font, remap + entry_index * 4, fullwidth_code | (glyph_index << 16))
        assignments.append({
            "victim_codepoint": f"U+{victim:04X}",
            "entry_index": entry_index,
            "new_codepoint": f"U+{fullwidth_code:04X}",
            "glyph_index": glyph_index,
            "target_page": target_page,
            "target_record": [dst_u, dst_v, src_width, src_height, target_page, src_vertical_offset],
            "source_record": list(ORIGINAL_DIGITS[digit]),
        })

    package[FONT_OFFSET:font_end] = font

    for texture_index, (location, raw, image) in page_objects.items():
        pixel_offset = texture_pixel_offset(raw)
        pixels = image.tobytes()
        raw[pixel_offset : pixel_offset + len(pixels)] = pixels
        package[location : location + len(raw)] = raw

    OUT_PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    OUT_PACKAGE.write_bytes(package)
    report = {
        "source_package": str(GOOD_PACKAGE),
        "output_package": str(OUT_PACKAGE),
        "package_size": len(package),
        "font_size": len(font),
        "font_records": count,
        "assignments": assignments,
        "sha256": hashlib.sha256(package).hexdigest().upper(),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "assignments"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
