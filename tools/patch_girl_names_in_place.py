from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rebuild_girl_names as base
import rebuild_shop_names_package as package_tools


GAME_ROOT = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game")
PACKAGE = GAME_ROOT / "CookedPC" / "GG2Game.u"
EXPANDED = base.EXPANDED
OUT_DIR = Path(r"D:\GALGUNVV\work\girl_names_in_place")
OUT_EXPANDED = OUT_DIR / "GG2Game.u.girl_names.in_place.expanded"
OUT_PACKAGE = OUT_DIR / "GG2Game.u.girl_names.in_place.modified"


def fstring(value: str) -> bytes:
    encoded = value.encode("utf-16-le") + b"\0\0"
    return struct.pack("<i", -(len(value) + 1)) + encoded


def patch_field(buffer: bytearray, object_offset: int, object_size: int, field: int, value: str) -> None:
    if not value:
        return
    object_data = bytes(buffer[object_offset : object_offset + object_size])
    needle = struct.pack("<II", field, 0) + struct.pack("<II", base.STR_PROPERTY, 0)
    position = object_data.find(needle)
    if position < 0:
        raise RuntimeError(f"missing field {field} at 0x{object_offset:X}")
    field_size = struct.unpack_from("<I", object_data, position + 16)[0]
    replacement = fstring(value)
    if len(replacement) > field_size:
        raise RuntimeError(
            f"name does not fit at 0x{object_offset:X}: {value!r} "
            f"needs {len(replacement)}, field has {field_size}"
        )
    start = object_offset + position + 24
    buffer[start : start + field_size] = replacement + b"\0" * (field_size - len(replacement))


def main() -> None:
    original_package = PACKAGE.read_bytes()
    expanded = bytearray(EXPANDED.read_bytes())
    if len(expanded) != base.EXPANDED.stat().st_size:
        raise RuntimeError("expanded package changed while reading")

    objects = base.object_boundaries()
    if len(objects) != 77:
        raise RuntimeError(f"expected 77 localized objects, found {len(objects)}")
    changed = 0
    for object_offset, object_size, key in objects:
        if key not in base.NAMES:
            raise RuntimeError(f"missing name mapping: {key}")
        first, last = base.NAMES[key]
        before = bytes(expanded[object_offset : object_offset + object_size])
        patch_field(expanded, object_offset, object_size, base.FIRST_NAME, first)
        patch_field(expanded, object_offset, object_size, base.LAST_NAME, last)
        if before != bytes(expanded[object_offset : object_offset + object_size]):
            changed += 1

    if changed != 77:
        raise RuntimeError(f"expected 77 changed objects, found {changed}")

    package_tools.lzo1x_literal_block = base.compress_lzo
    package_tools.CHUNK_INDEX = base.CHUNK_INDEX
    package_tools.BLOCK_INDEX = base.BLOCK_INDEX
    rebuilt = package_tools.rebuild_package(original_package, bytes(expanded))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_EXPANDED.write_bytes(expanded)
    OUT_PACKAGE.write_bytes(rebuilt)
    print(f"changed_objects={changed}")
    print(f"original_size={len(original_package)} rebuilt_size={len(rebuilt)}")
    print(f"output={OUT_PACKAGE}")


if __name__ == "__main__":
    main()
