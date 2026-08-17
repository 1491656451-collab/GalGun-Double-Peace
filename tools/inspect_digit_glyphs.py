from pathlib import Path
import struct

from build_cht_font_test import find_remap, parse_char_record


PACKAGE = Path(r"D:\GALGUNVV\GG2CNPatch_Distribution_Final_20260809\GG2Game\CookedPC\Startup_LOC_INT.upk")
RAW_ROOT = Path(
    r"D:\GALGUNVV\work\current_startup_builder\raw_extract\Startup_LOC_INT"
    r"\gg2_font\MessageFont"
)
FONT_OFFSET = 18236


def page_names() -> list[str]:
    return (
        ["MessageFont_PageA", "MessageFont_PageB"]
        + [f"MessageFont_Page{chr(code)}" for code in range(ord("C"), ord("Z") + 1)]
        + [f"MessageFont_PageB{chr(code)}" for code in range(ord("A"), ord("T") + 1)]
    )


def main() -> None:
    package = PACKAGE.read_bytes()
    raw_page_a = (RAW_ROOT / "MessageFont_PageA.Texture2D").read_bytes()
    page_a = package.find(raw_page_a[:128])
    font = package[FONT_OFFSET:page_a]
    count = struct.unpack_from("<i", font, 0x1C)[0]
    remap_offset, _ = find_remap(font, count)
    mapping = {
        struct.unpack_from("<HH", font, remap_offset + index * 4)[0]:
        struct.unpack_from("<HH", font, remap_offset + index * 4)[1]
        for index in range(count)
    }
    names = page_names()
    positions = {}
    for name in names:
        raw = (RAW_ROOT / f"{name}.Texture2D").read_bytes()
        positions[name] = package.find(raw[:128])
    print(f"font_offset={FONT_OFFSET} page_a={page_a} font_size={len(font)} records={count}")
    print("page_positions", [(name, positions[name]) for name in names[:4]])
    for code in range(ord("0"), ord("9") + 1):
        glyph = mapping.get(code)
        record = parse_char_record(font, glyph) if glyph is not None else None
        print(f"digit={chr(code)} glyph={glyph} record={record}")


if __name__ == "__main__":
    main()
