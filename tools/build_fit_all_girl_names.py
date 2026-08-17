from __future__ import annotations

import struct
from pathlib import Path
import sys

sys.path.insert(0, r"D:\GALGUNVV\work")
import rebuild_girl_names as girl
import rebuild_shop_names_package as package_tools


OUTPUT = Path(r"D:\GALGUNVV\work\girl_names_fit\GG2Game.u.modified")


def patch_field(buffer: bytearray, object_offset: int, object_size: int, field: int, value: str) -> bool:
    if not value:
        return False
    data = bytes(buffer[object_offset : object_offset + object_size])
    needle = struct.pack("<II", field, 0) + struct.pack("<II", girl.STR_PROPERTY, 0)
    pos = data.find(needle)
    if pos < 0:
        return False
    field_size = struct.unpack_from("<I", data, pos + 16)[0]
    old_value = data[pos + 24 : pos + 24 + field_size]
    old_length = struct.unpack_from("<I", old_value, 0)[0]
    capacity = old_length - 1
    try:
        encoded = value.encode("cp932")
    except UnicodeEncodeError:
        return False
    if len(encoded) > capacity:
        return False
    payload = struct.pack("<I", len(encoded) + (capacity - len(encoded)) + 1)
    payload += encoded + b" " * (capacity - len(encoded)) + b"\0"
    if len(payload) != field_size:
        return False
    start = object_offset + pos + 24
    buffer[start : start + field_size] = payload
    return True


def main() -> None:
    original = girl.PACKAGE.read_bytes()
    expanded = bytearray(girl.EXPANDED.read_bytes())
    changed = []
    for offset, size, key in girl.object_boundaries():
        first, last = girl.NAMES[key]
        fields = []
        if patch_field(expanded, offset, size, girl.FIRST_NAME, first):
            fields.append("first")
        if patch_field(expanded, offset, size, girl.LAST_NAME, last):
            fields.append("last")
        if fields:
            changed.append((key, fields))

    package_tools.CHUNK_INDEX = girl.CHUNK_INDEX
    package_tools.BLOCK_INDEX = girl.BLOCK_INDEX
    rebuilt = package_tools.rebuild_package(original, bytes(expanded))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(rebuilt)
    print(f"changed_objects={len(changed)} changed_fields={sum(len(v) for _, v in changed)}")
    print("skipped=" + ",".join(key for key, fields in changed if len(fields) < 2))
    print(f"output={OUTPUT}")


if __name__ == "__main__":
    main()
