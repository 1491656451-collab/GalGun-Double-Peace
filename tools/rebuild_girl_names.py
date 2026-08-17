from __future__ import annotations

import re
import struct
import subprocess
import tempfile
from pathlib import Path

import rebuild_shop_names_package as package_tools


ROOT = Path(r"D:\GALGUNVV")
WORK = ROOT / "work"
GAME_ROOT = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game")
PACKAGE = GAME_ROOT / "CookedPC" / "GG2Game.u"
EXPANDED = WORK / "gg2game_expanded_current_20260808" / "GG2Game.u"
# This list must be generated from the exact package being patched. The old
# shared list was produced from an earlier expanded package and contained
# stale serial sizes for unrelated defaults.
UMODEL_LIST = WORK / "umodel_list_current_before_girl_20260808.txt"
COMPRESSOR = WORK / "lzo_compress.exe"
OUTPUT_DIR = WORK / "girl_names_rebuild"
OUTPUT_EXPANDED = OUTPUT_DIR / "GG2Game.u.girl_names.expanded"
OUTPUT_PACKAGE = OUTPUT_DIR / "GG2Game.u.girl_names.modified"
INT_OUTPUT_DIR = OUTPUT_DIR / "Localization" / "INT"

FIRST_NAME = 12603
LAST_NAME = 20550
STR_PROPERTY = 30292
ENGLISH_LOCALIZED_START = 0x37EA41D
ENGLISH_LOCALIZED_END = 0x37F1180
CHUNK_INDEX = 56
BLOCK_INDEX = 6
EXPORT_OFFSET = 0x138C82
EXPORT_COUNT = 56902
EXPORT_ENTRY_SIZE = 0x44


# The source patch already used Traditional Chinese surnames in most entries.
# This completes the given names and normalizes the special characters too.
NAMES = {
    "00_NITTA_SAYAKA": ("\u65b0\u7530", "\u5f69\u52a0"),
    "01_KOKOROZAKI_MINA": ("\u5fc3\u5d0e", "\u7f8e\u5948"),
    "02_NIRA_MAOKO": ("\u97ee", "\u771f\u592e\u5b50"),
    "03_TENDOH_MEGUMI": ("\u5929\u9053", "\u60e0"),
    "04_KUCHIKI_KAZUSA": ("\u673d\u6728", "\u548c\u7d17"),
    "05_NIKAIDOH_AKI": ("\u4e8c\u968e\u5802", "\u4e9e\u7d00"),
    "06_SATSUKI_KOKO": ("\u76bf\u6708", "\u53ef\u53ef"),
    "07_NISHIGUCHI_TSUKASA": ("\u897f\u53e3", "\u53f8"),
    "08_HARUSAME_RION": ("\u6625\u96e8", "\u8389\u97f3"),
    "09_TERUMOTO_RINA": ("\u7167\u672c", "\u8389\u8863\u83dc"),
    "10_KUROSAWA_OTOME": ("\u9ed1\u6fa4", "\u4e59\u5973"),
    "11_AOSHIMA_MAI": ("\u9752\u5d8b", "\u9ebb\u8863"),
    "12_KOJIKA_SAYOKO": ("\u5c0f\u9e7f", "\u4f50\u4ee3\u5b50"),
    "13_SINONOME_KUSUMI": ("\u6771\u96f2", "\u4e45\u9808\u7f8e"),
    "14_HOSHIZORA_SHIHO": ("\u661f\u7a7a", "\u5fd7\u4fdd"),
    "15_SUDOH_MAKI": ("\u9808\u85e4", "\u771f\u7d00"),
    "16_ANITA_BELLMAN": ("\u8c9d\u723e\u66fc", "\u5b89\u59ae\u5854"),
    "17_MATSUBARA_MIHONO": ("\u677e\u539f", "\u7f8e\u7a57\u4e43"),
    "18_NANBARA_KAZUMI": ("\u5357\u539f", "\u4e00\u5df3"),
    "19_JINBO_YUKINA": ("\u795e\u4fdd", "\u96ea\u83dc"),
    "20_SHISHIDO_KANKO": ("\u5bb8\u6236", "\u7518\u5b50"),
    "21_AMATSUKA_PATAKO": ("\u5929\u4f7f", "\u5e15\u5854\u5b50"),
    "22_HARUNO_TSUBOMI": ("\u6625\u91ce", "\u854a"),
    "23_SAKAGUCHI_KASUMI": ("\u5742\u53e3", "\u971e"),
    "24_KIBAYASHI_KUMI": ("\u6728\u6797", "\u4e45\u7f8e"),
    "25_KOSUGI_NENEKO": ("\u5c0f\u6749", "\u5be7\u5be7\u5b50"),
    "26_TAKADA_SAKI": ("\u9ad8\u7530", "\u6c99\u5e0c"),
    "27_TSUKADA_FUMI": ("\u585a\u7530", "\u8299\u7f8e"),
    "28_KURODA_RIKO": ("\u9ed1\u7530", "\u8389\u5b50"),
    "29_NATSUKI_MARIA": ("\u590f\u6a39", "\u746a\u9e97\u4e9e"),
    "30_MURASAME_TSUZUMI": ("\u6751\u96e8", "\u9f13"),
    "31_TACHIBANA_TSUGUMI": ("\u6a58", "\u9db4"),
    "32_HANBA_MIDORI": ("\u534a\u5834", "\u7fe0"),
    "33_HITOTSUBASHI_JUNKO": ("\u4e00\u6a4b", "\u6df3\u5b50"),
    "34_KUMANO_MIKOTO": ("\u718a\u91ce", "\u7f8e\u7434"),
    "35_KUSE_HAYARI": ("\u4e45\u4e16", "\u65e9\u8389"),
    "36_MIKASA_RURIKO": ("\u4e09\u7b20", "\u7460\u7483\u5b50"),
    "37_HIMENO_RAN": ("\u59ec\u91ce", "\u862d"),
    "38_NISHIBINA_URARAKA": ("\u897f\u96db", "\u9e97"),
    "39_ISE_NANAMI": ("\u4f0a\u52e2", "\u5948\u83dc\u7f8e"),
    "40_SAZANAMI_KAREN": ("\u6f23", "\u53ef\u6190"),
    "41_AKAGI_KAHO": ("\u8d64\u6728", "\u590f\u5e06"),
    "42_TANAKA_RIKIKO": ("\u7530\u4e2d", "\u529b\u5b50"),
    "43_SUZUNO_MEI": ("\u9234\u91ce", "\u82bd\u8863"),
    "44_SAIJOH_KAZAMI": ("\u897f\u689d", "\u98a8\u898b"),
    "45_TSUKIMIYA_MADOKA": ("\u6708\u5bae", "\u5713"),
    "46_ASANO_SUZUME": ("\u671d\u91ce", "\u9234\u829d"),
    "47_SHIROGANE_YUKI": ("\u767d\u9280", "\u96ea"),
    "48_KURODA_MAKO": ("\u9ed1\u7530", "\u771f\u5b50"),
    "49_FUJIWARA_SAORI": ("\u85e4\u539f", "\u6c99\u7e54"),
    "50_WAKABA_MIRAI": ("\u82e5\u8449", "\u672a\u4f86"),
    "51_KUSUNOKI_MIHO": ("\u6950", "\u7f8e\u7a57"),
    "52_NAMIKI_SANGO": ("\u6ce2\u6728", "\u73ca\u745a"),
    "53_SUGURI_SAYU": ("\u6751\u4e3b", "\u5de6\u7531"),
    "54_SUGURI_YUYU": ("\u6751\u4e3b", "\u53f3\u7531"),
    "55_KOTOBUKI_RINGO": ("\u58fd", "\u6797\u6a94"),
    "56_GOZU_YURINA": ("\u725b\u982d", "\u767e\u5408\u83dc"),
    "57_YANAGIDA_MAFUYU": ("\u67f3\u7530", "\u771f\u51ac"),
    "58_SAITO_YUKA": ("\u9f4a\u85e4", "\u7531\u4f73"),
    "59_KUJIRAI_KONOMI": ("\u9be8\u4e95", "\u597d\u7f8e"),
    "60_TSURUGI_YURI": ("\u528d", "\u60a0\u68a8"),
    "61_MASAMI_AKIKO": ("\u6b63\u898b", "\u4e9e\u7d00\u5b50"),
    "62_YOSHIKAWA_REN": ("\u5409\u5ddd", "\u6200"),
    "63_NINOMIYA_SHIZUKA": ("\u4e8c\u5bae", "\u975c\u9999"),
    "64_FUJINO_SAORI": ("\u85e4\u91ce", "\u6c99\u7e54"),
    "65_AZUMA_MICHIYO": ("\u6771", "\u7f8e\u5343\u4ee3"),
    "66_KURIBAYASHI_RENA": ("\u6817\u6797", "\u6021\u5948"),
    "67_HATTORI_ASUKA": ("\u670d\u90e8", "\u660e\u65e5\u9999"),
    "68_KURASHIKI_KIRARA": ("\u5009\u6577", "\u7dba\u7f85\u7f85"),
    "69_KAMIZONO_SHINOBU": ("\u795e\u5712", "\u5fcd"),
    "70_KAMIZONO_MAYA": ("\u795e\u5712", "\u771f\u591c"),
    "71_EKORO": ("", "\u827e\u53ef\u863f"),
    "72_KURONA": ("", "\u5eab\u863f\u5a1c"),
    "73_PATAKO": ("", "\u5e15\u5854\u5b50"),
    "74_UNO_AOI": ("\u5154\u91ce", "\u8475"),
    "75_FINAL_YUREINO_YUKO": ("\u904a\u9748\u91ce", "\u5e7d\u5b50"),
    "76_YUREINO_YUKO": ("\u672a\u77e5", "\u672a\u77e5"),
    "77_SHIAWASE_HUMAN": ("\u5e78\u798f", "\u4eba"),
    "78_FUSHIAWASE_HUMAN": ("\u4e0d\u5e78\u798f", "\u4eba"),
}

def fstring(value: str) -> bytes:
    encoded = value.encode("utf-16-le") + b"\0\0"
    return struct.pack("<i", -(len(value) + 1)) + encoded


def object_boundaries() -> list[tuple[int, int, str]]:
    text = UMODEL_LIST.read_bytes().decode("utf-16")
    if "GG2Game.u" not in text or "D:/SteamLibrary/steamapps/common/GalGun Double Peace" not in text:
        raise RuntimeError(f"UModel list is not from the current GG2Game.u: {UMODEL_LIST}")
    result = []
    pattern = re.compile(
        r"^\s*\d+\s+([0-9A-F]+)\s+([0-9A-F]+)\s+GG2GirlLocalizedData\s+(\S+)\s*$"
    )
    for line in text.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        offset = int(match.group(1), 16)
        if ENGLISH_LOCALIZED_START <= offset < ENGLISH_LOCALIZED_END:
            result.append((offset, int(match.group(2), 16), match.group(3)))
    if len(result) != 77:
        raise RuntimeError(f"expected 77 English localized objects, found {len(result)}")
    return result


def patch_localized_object(data: bytes, first: str, last: str) -> tuple[bytes, int]:
    replacements = []
    for field, target in ((FIRST_NAME, first), (LAST_NAME, last)):
        if not target:
            continue
        needle = struct.pack("<II", field, 0) + struct.pack("<II", STR_PROPERTY, 0)
        position = data.find(needle)
        if position < 0:
            raise RuntimeError(f"missing field {field} in localized object")
        old_size = struct.unpack_from("<I", data, position + 16)[0]
        old_value = data[position + 24 : position + 24 + old_size]
        replacement_value = fstring(target)
        header = bytearray(data[position : position + 24])
        struct.pack_into("<I", header, 16, len(replacement_value))
        replacements.append(
            (position, 24 + old_size, bytes(header) + replacement_value, target, old_value)
        )

    replacements.sort()
    result = bytearray()
    cursor = 0
    for position, old_total, replacement, _, _ in replacements:
        result.extend(data[cursor:position])
        result.extend(replacement)
        cursor = position + old_total
    result.extend(data[cursor:])
    delta = len(result) - len(data)
    return bytes(result), delta


def patch_package_expanded(
    expanded: bytes, package: bytes
) -> tuple[bytes, list[int], list[int]]:
    infos = [
        package_tools.chunk_info(package, i)
        for i in range(package_tools.u32(package, package_tools.CHUNK_COUNT_OFFSET))
    ]
    chunk_start, _, _, _, block_size, _, _ = infos[CHUNK_INDEX]
    block_start = chunk_start + BLOCK_INDEX * block_size
    block_end = block_start + block_size
    objects = object_boundaries()
    object_deltas = {}
    result = bytearray()
    cursor = block_start
    total_delta = 0
    for offset, size, key in objects:
        if key not in NAMES:
            raise RuntimeError(f"missing name mapping: {key}")
        patched, delta = patch_localized_object(
            expanded[offset : offset + size], *NAMES[key]
        )
        result.extend(expanded[cursor:offset])
        result.extend(patched)
        cursor = offset + size
        object_deltas[offset] = delta
        total_delta += delta
        print(f"{key}: {NAMES[key][0]} {NAMES[key][1]} delta={delta}")
    result.extend(expanded[cursor:block_end])
    if total_delta > 0:
        raise RuntimeError(f"localized data block grew by {total_delta} bytes")
    result.extend(b"\0" * (-total_delta))
    if len(result) != block_end - block_start:
        raise RuntimeError("localized data block size changed")

    patched_expanded = bytearray(expanded)
    patched_expanded[block_start:block_end] = result

    # The export table stores the serial size and absolute uncompressed offset
    # for every object. Expanding one object shifts all later objects in this
    # block, so update those two fields before rebuilding the LZO blocks.
    changed_export_positions = []
    for index in range(EXPORT_COUNT):
        entry = EXPORT_OFFSET + index * EXPORT_ENTRY_SIZE
        old_size = package_tools.u32(expanded, entry + 0x20)
        old_offset = package_tools.u32(expanded, entry + 0x24)
        if not (block_start <= old_offset < block_end):
            continue
        shift = sum(delta for offset, delta in object_deltas.items() if offset < old_offset)
        new_offset = old_offset + shift
        new_size = old_size + object_deltas.get(old_offset, 0)
        package_tools.put_u32(patched_expanded, entry + 0x20, new_size)
        package_tools.put_u32(patched_expanded, entry + 0x24, new_offset)
        changed_export_positions.extend((entry + 0x20, entry + 0x24))

    if not changed_export_positions:
        raise RuntimeError("no export records were updated")
    return bytes(patched_expanded), list(object_deltas), changed_export_positions


def patch_int(source: Path, destination: Path) -> None:
    text = source.read_bytes().decode("utf-16")
    for key, (first, last) in NAMES.items():
        match = re.search(
            rf"(?ms)^\[localizedData\.{re.escape(key)}.*?(?=^\[localizedData\.|\Z)",
            text,
        )
        if not match:
            raise RuntimeError(f"missing INT block: {key}")
        block = match.group(0)
        if first:
            block, count = re.subn(
                r"(?m)^firstName=\"[^\"]*\"\r*$",
                f'firstName="{first}"',
                block,
                count=1,
            )
            if count != 1:
                raise RuntimeError(f"missing firstName field: {key}")
        if last:
            block, count = re.subn(
                r"(?m)^lastName=\"[^\"]*\"\r*$",
                f'lastName="{last}"',
                block,
                count=1,
            )
            if count != 1:
                raise RuntimeError(f"missing lastName field: {key}")
        text = text[: match.start()] + block + text[match.end() :]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(b"\xff\xfe" + text.encode("utf-16-le"))


def compress_lzo(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="gg2_girls_", dir=WORK) as temp:
        temp_dir = Path(temp)
        raw = temp_dir / "block.raw"
        compressed = temp_dir / "block.lzo"
        raw.write_bytes(data)
        subprocess.run([str(COMPRESSOR), str(raw), str(compressed)], check=True)
        return compressed.read_bytes()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    expanded = EXPANDED.read_bytes()
    original = PACKAGE.read_bytes()
    patched_expanded, object_positions, export_positions = patch_package_expanded(
        expanded, original
    )

    package_tools.lzo1x_literal_block = compress_lzo
    infos = [
        package_tools.chunk_info(original, i)
        for i in range(package_tools.u32(original, package_tools.CHUNK_COUNT_OFFSET))
    ]
    affected = {(CHUNK_INDEX, BLOCK_INDEX)}
    for position in export_positions:
        for index, info in enumerate(infos):
            start, _, _, _, block_size, _, _ = info
            if start <= position < start + info[1]:
                affected.add((index, (position - start) // block_size))
                break
        else:
            raise RuntimeError(f"export position outside chunks: {position:#x}")

    rebuilt = original
    for chunk_index, block_index in sorted(affected):
        package_tools.CHUNK_INDEX = chunk_index
        package_tools.BLOCK_INDEX = block_index
        rebuilt = package_tools.rebuild_package(rebuilt, patched_expanded)
    OUTPUT_EXPANDED.write_bytes(patched_expanded)
    OUTPUT_PACKAGE.write_bytes(rebuilt)

    for filename in ("GG2GirlDatas.int", "GG2GirlDatas_Eng.int"):
        patch_int(GAME_ROOT / "Localization" / "INT" / filename, INT_OUTPUT_DIR / filename)

    print(f"expanded={len(patched_expanded)} package={len(rebuilt)}")
    print(f"package={OUTPUT_PACKAGE}")


if __name__ == "__main__":
    main()
