from pathlib import Path
import re
import struct

from build_cht_font_test import find_remap, parse_char_record


PATCH_ROOT = Path(r"D:\GALGUNVV\GG2CNPatch_Distribution_Final_20260809")
FONT_PACKAGE = PATCH_ROOT / "GG2Game/CookedPC/Startup_LOC_INT.upk"
RAW_PAGE_A = Path(
    r"D:\GALGUNVV\work\current_startup_builder\raw_extract\Startup_LOC_INT"
    r"\gg2_font\MessageFont\MessageFont_PageA.Texture2D"
)
GAME_ROOT = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace")
OPENING_SOURCE = Path(
    r"D:\Unreal\GALGUN汉化源文件\GG2CNPatch_Distribution\Opening\Opening.umap"
)

FIELD_RE = re.compile(r'(?:(?P<key>[A-Za-z_]\w*)(?:\[\d+\])?=|m_levelName\[\d+\]=)"(?P<value>[^"]*)"')
DISPLAY_KEYS = {"Text", "profileText", "firstName", "lastName", "UnknownName"}


def load_font_mapping() -> tuple[bytes, set[int], int, int]:
    package = FONT_PACKAGE.read_bytes()
    page_a = package.find(RAW_PAGE_A.read_bytes()[:128])
    if page_a <= 0:
        raise RuntimeError("Could not locate MessageFont_PageA in the patch package")
    font = package[18236:page_a]
    count = struct.unpack_from("<i", font, 0x1C)[0]
    remap_offset, _ = find_remap(font, count)
    mapping = {
        struct.unpack_from("<HH", font, remap_offset + index * 4)[0]
        for index in range(count)
    }
    bad_records = []
    for index in range(count):
        start_u, start_v, width, height, page, _ = parse_char_record(font, index)
        if width < 0 or height < 0 or page >= 46:
            bad_records.append((index, start_u, start_v, width, height, page))
    if bad_records:
        raise RuntimeError(f"Invalid font records: {bad_records[:3]}")
    return font, mapping, count, page_a


def verify_display_fields(mapping: set[int]) -> tuple[int, set[str], set[int]]:
    root = PATCH_ROOT / "GG2Game/Localization/INT"
    fields = 0
    files_with_missing: set[str] = set()
    missing: set[int] = set()
    for path in root.glob("*.int"):
        text = path.read_bytes().decode("utf-16")
        for line in text.splitlines():
            for match in FIELD_RE.finditer(line):
                key = match.group("key") or "m_levelName"
                if key == "PawnName":
                    continue
                if key != "m_levelName" and key not in DISPLAY_KEYS and not key.endswith("Text"):
                    continue
                fields += 1
                for char in match.group("value"):
                    code = ord(char)
                    if code > 127 and code not in mapping:
                        missing.add(code)
                        files_with_missing.add(path.name)
    return fields, files_with_missing, missing


def verify_manifest() -> int:
    manifest = PATCH_ROOT / "manifest_sha256.txt"
    count = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9A-Fa-f]{64})  (.+)", line)
        if not match:
            raise RuntimeError(f"Invalid manifest line: {line}")
        relative = match.group(2).replace("/", "\\")
        path = PATCH_ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"Missing manifest file: {relative}")
        import hashlib

        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        if digest != match.group(1).upper():
            raise RuntimeError(f"Manifest hash mismatch: {relative}")
        count += 1
    return count


def main() -> None:
    _, mapping, count, page_a = load_font_mapping()
    fields, missing_files, missing = verify_display_fields(mapping)
    legacy_japanese = {code for code in missing if 0x3040 <= code <= 0x30FF}
    unsupported = missing - legacy_japanese
    if unsupported:
        raise RuntimeError(
            f"Missing non-Japanese display glyphs: "
            f"{sorted(f'U+{code:04X}' for code in unsupported)}"
        )
    for name in ("levelList.int", "levelList_Eng.INT"):
        path = PATCH_ROOT / "GG2Game/Localization/INT" / name
        text = path.read_bytes().decode("utf-16")
        entries = [line for line in text.splitlines() if line.startswith("m_levelName[")]
        if len(entries) != 250 or re.search(r"[\u3040-\u30FF]", text):
            raise RuntimeError(f"Invalid level list coverage: {name}")
    manifest_count = verify_manifest()
    opening = PATCH_ROOT / "GG2Game/CookedPC/Maps/Opening/Opening.umap"
    if opening.read_bytes() != OPENING_SOURCE.read_bytes():
        raise RuntimeError("Opening.umap does not match the requested source")
    print(
        f"font_records={count} pageA_offset={page_a} display_fields={fields} "
        f"missing_nonJapanese_display_glyphs=0 legacy_Japanese_codepoints={len(legacy_japanese)} "
        f"levelLists=250+250 manifest_entries={manifest_count}"
    )


if __name__ == "__main__":
    main()
