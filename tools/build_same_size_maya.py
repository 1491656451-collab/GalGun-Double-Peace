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
UMODEL_LIST = WORK / "umodel_list_current_before_girl_20260808.txt"
JPN_NAMES = GAME_ROOT / "Localization" / "JPN" / "GG2GirlDatas.jpn"
COMPRESSOR = WORK / "lzo_compress.exe"
OUT_DIR = WORK / "same_size_maya_jpn"
OUT_EXPANDED = OUT_DIR / "GG2Game.u.expanded"
OUT_PACKAGE = OUT_DIR / "GG2Game.u"

CHUNK_INDEX = 56
BLOCK_INDEX = 6
ENGLISH_LOCALIZED_START = 0x37EA41D
ENGLISH_LOCALIZED_END = 0x37F1180
EXPORT_COUNT = 56902
EXPORT_OFFSET = 0x138C82
EXPORT_ENTRY_SIZE = 0x44
FIRST_NAME = 12603
LAST_NAME = 20550
STR_PROPERTY = 30292


def read_japanese_names() -> dict[str, tuple[str, str]]:
    text = JPN_NAMES.read_bytes().decode("cp932")
    result: dict[str, tuple[str, str]] = {}
    pattern = re.compile(
        r"(?ms)^\[localizedData\.([^ ]+) GG2GirlLocalizedData\].*?"
        r"^firstName=\"([^\"]*)\"\s*$.*?"
        r"^lastName=\"([^\"]*)\"\s*$"
    )
    for match in pattern.finditer(text):
        result[match.group(1)] = (match.group(2), match.group(3))
    if len(result) != 79:
        raise RuntimeError(f"expected 79 Japanese names, found {len(result)}")
    return result


def object_boundaries() -> list[tuple[int, int, str]]:
    text = UMODEL_LIST.read_bytes().decode("utf-16")
    pattern = re.compile(
        r"^\s*\d+\s+([0-9A-F]+)\s+([0-9A-F]+)\s+GG2GirlLocalizedData\s+(\S+)\s*$"
    )
    result = []
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


def patch_field(data: bytes, field: int, target: str) -> tuple[bytes, bool]:
    if not target:
        return data, False
    needle = struct.pack("<II", field, 0) + struct.pack("<II", STR_PROPERTY, 0)
    position = data.find(needle)
    if position < 0:
        raise RuntimeError(f"missing field {field}")

    value_size = struct.unpack_from("<I", data, position + 16)[0]
    old_value = data[position + 24 : position + 24 + value_size]
    if len(old_value) != value_size or value_size < 5:
        raise RuntimeError(f"invalid FString field {field}: size={value_size}")
    old_length = struct.unpack_from("<I", old_value, 0)[0]
    if old_length <= 0 or old_length + 4 != value_size:
        raise RuntimeError(f"unexpected ANSI FString field {field}: {old_value!r}")

    encoded = target.encode("cp932")
    capacity = old_length - 1
    if len(encoded) > capacity:
        raise RuntimeError(
            f"Japanese value {target!r} needs {len(encoded)} bytes, "
            f"but {capacity} are available for field {field}"
        )
    payload = encoded + (b" " * (capacity - len(encoded))) + b"\0"
    replacement = struct.pack("<I", len(payload)) + payload
    if len(replacement) != value_size:
        raise RuntimeError("same-size replacement failed")
    result = bytearray(data)
    result[position + 24 : position + 24 + value_size] = replacement
    return bytes(result), True


def patch_object(data: bytes, first: str, last: str) -> tuple[bytes, int]:
    result = data
    changed = 0
    result, did_change = patch_field(result, FIRST_NAME, first)
    changed += int(did_change)
    result, did_change = patch_field(result, LAST_NAME, last)
    changed += int(did_change)
    if len(result) != len(data):
        raise RuntimeError("localized object changed size")
    return result, changed


def compress_block(raw: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="gg2_same_size_", dir=WORK) as temp:
        temp_dir = Path(temp)
        source = temp_dir / "block.raw"
        output = temp_dir / "block.lzo"
        source.write_bytes(raw)
        subprocess.run([str(COMPRESSOR), str(source), str(output)], check=True)
        return output.read_bytes()


def rebuild_package(original: bytes, expanded: bytes) -> bytes:
    infos = [
        package_tools.chunk_info(original, i)
        for i in range(package_tools.u32(original, package_tools.CHUNK_COUNT_OFFSET))
    ]
    package_tools.CHUNK_INDEX = CHUNK_INDEX
    package_tools.BLOCK_INDEX = BLOCK_INDEX
    return package_tools.rebuild_package(original, expanded)


def main() -> None:
    names = read_japanese_names()
    original = EXPANDED.read_bytes()
    patched = bytearray(original)
    total_changed = 0
    targets = {
        key: (offset, size)
        for offset, size, key in object_boundaries()
        if key == "70_KAMIZONO_MAYA"
    }
    if set(targets) != {"70_KAMIZONO_MAYA"}:
        raise RuntimeError("Maya object boundary was not found")
    for key, (offset, size) in targets.items():
        object_data, changed = patch_object(
            original[offset : offset + size], *names[key]
        )
        patched[offset : offset + size] = object_data
        total_changed += changed
    patched = bytes(patched)
    if len(patched) != len(original):
        raise RuntimeError("expanded package size changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_EXPANDED.write_bytes(patched)
    OUT_PACKAGE.write_bytes(rebuild_package(PACKAGE.read_bytes(), patched))
    print(f"changed_fields={total_changed}")
    print(f"expanded_size={len(patched)} package_size={OUT_PACKAGE.stat().st_size}")
    print(f"output={OUT_PACKAGE}")


if __name__ == "__main__":
    main()
