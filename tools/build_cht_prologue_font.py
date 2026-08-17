from __future__ import annotations

import argparse
import csv
import re
import shutil
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PATCH_ROOT = Path(r"D:\GALGUNVV\work\cht_font_test_builder")
GAME_ROOT = PATCH_ROOT.parent
RAW_ROOT = PATCH_ROOT / "raw_extract" / "Startup_LOC_INT"
DECOMPRESSED_PACKAGE = PATCH_ROOT / "decompressed" / "Startup_LOC_INT.upk"
OUT_PACKAGE = Path(r"D:\\GALGUNVV\\work\\cht_prologue_font_output\\Startup_LOC_INT.cht_prologue.upk")
TRANSLATIONS_CSV = PATCH_ROOT / "translations_int.csv"
UI_TRANSLATIONS_CSV = PATCH_ROOT / "ui_translations_int.csv"
EXTRA_FONT_CHARS_FILE = PATCH_ROOT / "extra_font_chars.txt"
REPORT = Path(r"D:\\GALGUNVV\\work\\cht_prologue_font_output\\font_patch_report.txt")

FONT_OBJECT = RAW_ROOT / "gg2_font" / "MessageFont.Font"
TEXTURE_ROOT = RAW_ROOT / "gg2_font" / "MessageFont"
WINDOWS_FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\msyhbd.ttc"),
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\simsun.ttc"),
]

PAGE_NAMES = (
    ["MessageFont_PageA", "MessageFont_PageB"]
    + [f"MessageFont_Page{chr(c)}" for c in range(ord("C"), ord("Z") + 1)]
    + [f"MessageFont_PageB{chr(c)}" for c in range(ord("A"), ord("T") + 1)]
)

EXTRA_TEST_CHARS = (
    "这们说话爱很只歉惜找或刚假"
    "个倒像先别动后学开关国过还进来没体简试测吗呢吧啊她他"
    "，。！？、：；（）《》“”‘’……"
)


def i32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<i", data, offset)[0]


def put_i32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<i", data, offset, value)


def parse_char_record(data: bytes | bytearray, index: int) -> tuple[int, int, int, int, int, int]:
    offset = 0x20 + index * 21
    start_u, start_v, width, height = struct.unpack_from("<iiii", data, offset)
    texture_index = data[offset + 16]
    vertical_offset = i32(data, offset + 17)
    return start_u, start_v, width, height, texture_index, vertical_offset


def find_remap(font_data: bytes | bytearray, char_count: int) -> tuple[int, int]:
    marker = struct.pack("<ii", 80, 0)
    expected_size = 12 + char_count * 4
    for offset in range(len(font_data) - expected_size, 0, -1):
        if font_data[offset : offset + 8] != marker:
            continue
        if i32(font_data, offset + 8) == char_count:
            return offset + 12, char_count
    raise RuntimeError("Could not find MessageFont remap table.")


def texture_pixel_offset(texture_data: bytes) -> int:
    # UE3 Texture2D with PF_G8 in this game stores the only mip's pixels here.
    # UModel exports the exact same bytes from this offset.
    return 0x172


def texture_size(texture_data: bytes) -> tuple[int, int]:
    # These fields are stable for the extracted Texture2D objects:
    # property SizeX value at 0x1c, SizeY value at 0x38.
    return i32(texture_data, 0x1C), i32(texture_data, 0x38)


def collect_patch_chars(extra_chars: str) -> list[str]:
    chars: list[str] = []
    seen: set[str] = set()

    def add_char(ch: str) -> None:
        if 0x80 <= ord(ch) <= 0xFFFF and not ch.isspace() and ch not in seen:
            chars.append(ch)
            seen.add(ch)

    def add_text(value: str) -> None:
        for ch in value:
            add_char(ch)

    # Manual missing-glyph reports are highest priority. The font has limited
    # spare slots, so these should not be pushed out by newly translated text.
    add_text(extra_chars)
    if EXTRA_FONT_CHARS_FILE.exists():
        add_text(EXTRA_FONT_CHARS_FILE.read_text(encoding="utf-8-sig"))

    if TRANSLATIONS_CSV.exists():
        with TRANSLATIONS_CSV.open("r", encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                for field in ("zh_name", "zh_text"):
                    add_text(row.get(field, ""))

    if UI_TRANSLATIONS_CSV.exists():
        with UI_TRANSLATIONS_CSV.open("r", encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                value = row.get("zh", "")
                # Unchanged source rows belong to the original language branch.
                # The patch targets *_ENG.int, so they do not need new glyphs.
                if value and value == row.get("source", ""):
                    continue
                add_text(value)

    return chars


def choose_system_font() -> Path:
    for path in WINDOWS_FONT_CANDIDATES:
        if path.exists():
            return path
    raise RuntimeError("No Chinese system font found under C:\\Windows\\Fonts.")


def is_cjk_or_fullwidth(char: str) -> bool:
    code = ord(char)
    return (
        0x3400 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or 0x3000 <= code <= 0x303F
        or 0xFF00 <= code <= 0xFFEF
        or char in "，。！？、：；（）《》“”’…—「」【】"
    )


def is_punctuation(char: str) -> bool:
    return char in "，。！？、：；（）《》“”’…—「」【】"


def font_size_candidates(char: str, width: int, height: int) -> range:
    if is_punctuation(char):
        start = min(39, height + 7)
    elif is_cjk_or_fullwidth(char):
        start = min(36, height + 5)
    else:
        start = min(34, height + 4)
    return range(start, 13, -1)


def fit_font(font_path: Path, char: str, width: int, height: int) -> tuple[ImageFont.FreeTypeFont, tuple[int, int, int, int]]:
    # Keep CJK glyphs visually uniform. The old per-glyph shrink-to-fit made
    # sparse glyphs like "?" and punctuation look much smaller than neighbors.
    for size in font_size_candidates(char, width, height):
        font = ImageFont.truetype(str(font_path), size=size)
        bbox = font.getbbox(char)
        margin = 2 if is_cjk_or_fullwidth(char) else 1
        if bbox[2] - bbox[0] <= width - margin and bbox[3] - bbox[1] <= height - margin:
            return font, bbox
    font = ImageFont.truetype(str(font_path), size=14)
    return font, font.getbbox(char)


def draw_glyph(page: Image.Image, font_path: Path, char: str, rect: tuple[int, int, int, int]) -> None:
    start_u, start_v, width, height = rect
    draw = ImageDraw.Draw(page)
    draw.rectangle((start_u, start_v, start_u + width - 1, start_v + height - 1), fill=0)
    font, bbox = fit_font(font_path, char, width, height)
    glyph_w = bbox[2] - bbox[0]
    glyph_h = bbox[3] - bbox[1]
    x = start_u + max(0, (width - glyph_w) // 2) - bbox[0]
    y = start_v + max(0, (height - glyph_h) // 2) - bbox[1]
    stroke_width = 1 if is_cjk_or_fullwidth(char) else 0
    if char in "一丨｜—":
        stroke_width = 2
    draw.text((x, y), char, font=font, fill=255, stroke_width=stroke_width, stroke_fill=255)


def update_package_blob(package_data: bytearray, old_blob: bytes, new_blob: bytes, label: str) -> None:
    if len(old_blob) != len(new_blob):
        raise RuntimeError(f"{label} size changed: {len(old_blob)} -> {len(new_blob)}")
    location = package_data.find(old_blob)
    if location < 0:
        raise RuntimeError(f"Could not locate {label} in decompressed package.")
    package_data[location : location + len(new_blob)] = new_blob


def build_font_patch(extra_chars: str) -> tuple[int, Path]:
    if not FONT_OBJECT.exists() or not DECOMPRESSED_PACKAGE.exists():
        raise RuntimeError("Run the extraction/decompression step first; required font sources are missing.")

    font_path = choose_system_font()
    desired_chars = collect_patch_chars(extra_chars)
    font_data = bytearray(FONT_OBJECT.read_bytes())
    char_count = i32(font_data, 0x1C)
    remap_offset, remap_count = find_remap(font_data, char_count)

    remap: list[tuple[int, int]] = []
    code_to_entries: dict[int, list[int]] = {}
    for entry in range(remap_count):
        offset = remap_offset + entry * 4
        code = struct.unpack_from("<H", font_data, offset)[0]
        glyph_index = struct.unpack_from("<H", font_data, offset + 2)[0]
        remap.append((code, glyph_index))
        code_to_entries.setdefault(code, []).append(entry)

    desired_codes = {ord(ch) for ch in desired_chars}

    # English localization only needs printable ASCII from the source atlas.
    # Every translated character is repacked so all CJK glyphs use one size.
    def preserve_source_code(code: int) -> bool:
        # Keep fullwidth HUD digits as well as printable ASCII.
        return 0x20 <= code < 0x7F or 0xFF10 <= code <= 0xFF19

    protected_indices = {
        glyph_index
        for code, glyph_index in remap
        if preserve_source_code(code)
    }
    available_indices = [
        glyph_index
        for glyph_index in range(char_count)
        if glyph_index not in protected_indices
    ]
    if len(available_indices) < len(desired_chars):
        raise RuntimeError(
            f"Not enough font records: need {len(desired_chars)}, have {len(available_indices)}."
        )

    available_entries = [
        entry
        for entry, (code, _) in enumerate(remap)
        if code not in desired_codes and not preserve_source_code(code)
    ]
    new_codes = [ch for ch in desired_chars if ord(ch) not in code_to_entries]
    if len(available_entries) < len(new_codes):
        raise RuntimeError(
            f"Not enough remap entries: need {len(new_codes)}, have {len(available_entries)}."
        )

    textures: dict[int, tuple[bytearray, Image.Image, Path]] = {}
    for texture_index, page_name in enumerate(PAGE_NAMES):
        path = TEXTURE_ROOT / f"{page_name}.Texture2D"
        raw = bytearray(path.read_bytes())
        width, height = texture_size(raw)
        pixel_offset = texture_pixel_offset(raw)
        pixels = bytes(raw[pixel_offset : pixel_offset + width * height])
        textures[texture_index] = (raw, Image.frombytes("L", (width, height), pixels), path)

    glyph_width = 36
    glyph_height = 34
    occupancy: dict[int, bytearray] = {}
    texture_dimensions: dict[int, tuple[int, int]] = {}
    for texture_index, (raw, _, _) in textures.items():
        width, height = texture_size(raw)
        texture_dimensions[texture_index] = (width, height)
        occupancy[texture_index] = bytearray(width * height)

    def mark_rect(texture_index: int, x: int, y: int, width: int, height: int) -> None:
        page_width, page_height = texture_dimensions[texture_index]
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(page_width, x + width)
        y1 = min(page_height, y + height)
        if x1 <= x0 or y1 <= y0:
            return
        row = b"\x01" * (x1 - x0)
        for yy in range(y0, y1):
            offset = yy * page_width + x0
            occupancy[texture_index][offset : offset + len(row)] = row

    for glyph_index in protected_indices:
        start_u, start_v, width, height, texture_index, _ = parse_char_record(font_data, glyph_index)
        if texture_index < len(PAGE_NAMES) and width > 0 and height > 0:
            mark_rect(texture_index, start_u, start_v, width, height)

    def region_is_free(texture_index: int, x: int, y: int) -> bool:
        page_width, _ = texture_dimensions[texture_index]
        page = occupancy[texture_index]
        for yy in range(y, y + glyph_height):
            offset = yy * page_width + x
            if any(page[offset : offset + glyph_width]):
                return False
        return True

    packed_rects: list[tuple[int, int, int, int, int]] = []
    for texture_index in range(len(PAGE_NAMES)):
        page_width, page_height = texture_dimensions[texture_index]
        for y in range(0, page_height - glyph_height + 1):
            x = 0
            while x <= page_width - glyph_width:
                if region_is_free(texture_index, x, y):
                    packed_rects.append((x, y, glyph_width, glyph_height, texture_index))
                    mark_rect(texture_index, x, y, glyph_width, glyph_height)
                    x += glyph_width
                    if len(packed_rects) >= len(desired_chars):
                        break
                else:
                    x += 1
            if len(packed_rects) >= len(desired_chars):
                break
        if len(packed_rects) >= len(desired_chars):
            break

    if len(packed_rects) < len(desired_chars):
        raise RuntimeError(
            f"Not enough atlas space: need {len(desired_chars)}, packed {len(packed_rects)}."
        )

    assignments: dict[str, int] = {}
    victim_iter = iter(available_entries)
    for ch, glyph_index, rect in zip(desired_chars, available_indices, packed_rects):
        start_u, start_v, width, height, texture_index = rect
        record_offset = 0x20 + glyph_index * 21
        struct.pack_into("<iiii", font_data, record_offset, start_u, start_v, width, height)
        font_data[record_offset + 16] = texture_index
        put_i32(font_data, record_offset + 17, 7)

        code = ord(ch)
        existing_entries = code_to_entries.get(code, [])
        if existing_entries:
            for entry in existing_entries:
                put_i32(font_data, remap_offset + entry * 4, code | (glyph_index << 16))
        else:
            entry = next(victim_iter)
            put_i32(font_data, remap_offset + entry * 4, code | (glyph_index << 16))
        assignments[ch] = glyph_index

    for ch, glyph_index in assignments.items():
        start_u, start_v, width, height, texture_index, _ = parse_char_record(font_data, glyph_index)
        draw_glyph(textures[texture_index][1], font_path, ch, (start_u, start_v, width, height))

    package_data = bytearray(DECOMPRESSED_PACKAGE.read_bytes())
    update_package_blob(package_data, FONT_OBJECT.read_bytes(), bytes(font_data), "MessageFont.Font")

    for texture_index, (raw, page, path) in textures.items():
        pixel_offset = texture_pixel_offset(raw)
        pixels = page.tobytes()
        raw[pixel_offset : pixel_offset + len(pixels)] = pixels
        update_package_blob(package_data, path.read_bytes(), bytes(raw), PAGE_NAMES[texture_index])

    OUT_PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    OUT_PACKAGE.write_bytes(package_data)

    assigned_indices = list(assignments.values())
    duplicate_indices = len(assigned_indices) - len(set(assigned_indices))
    missing_chars = [ch for ch in desired_chars if ch not in assignments]

    with REPORT.open("w", encoding="utf-8") as fh:
        fh.write(f"Font source: {font_path}\n")
        fh.write(f"Requested characters: {len(desired_chars)}\n")
        fh.write(f"Patched characters: {len(assignments)}\n")
        fh.write(f"Protected ASCII glyphs: {len(protected_indices)}\n")
        fh.write(f"Packed atlas rectangles: {len(packed_rects)}\n")
        fh.write(f"Unused font records: {len(available_indices) - len(assignments)}\n")
        fh.write(f"Duplicate glyph assignments: {duplicate_indices}\n")
        fh.write("\nAssigned characters:\n")
        fh.write("".join(assignments) + "\n")
        if missing_chars:
            fh.write("\nMissing characters:\n")
            fh.write("".join(missing_chars) + "\n")

    if duplicate_indices or missing_chars:
        raise RuntimeError(
            f"Font allocation failed: duplicates={duplicate_indices}, missing={len(missing_chars)}."
        )

    return len(assignments), OUT_PACKAGE


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extra-chars", default=EXTRA_TEST_CHARS)
    args = parser.parse_args()
    count, out_path = build_font_patch(args.extra_chars)
    print(f"Built font patch: {out_path}")
    print(f"Patched characters: {count}")
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()

# Test override: use only the supplied Traditional Chinese sample characters.
EXTRA_TEST_CHARS = ''



