from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rebuild_girl_names as girl
import rebuild_shop_names_package as package_tools


OUT_DIR = Path(r"D:\GALGUNVV\work\girl_names_padded_package")
OUT_EXPANDED = OUT_DIR / "GG2Game.u.girl_names.padded.expanded"
OUT_PACKAGE = OUT_DIR / "GG2Game.u.girl_names.padded.modified"


def u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def block_locations(package: bytes, chunk_index: int) -> list[tuple[int, int, int]]:
    info = package_tools.chunk_info(package, chunk_index)
    compressed_offset = info[2]
    header_size = info[6]
    cursor = compressed_offset + header_size
    result = []
    for index in range(info[5]):
        compressed_size, raw_size = struct.unpack_from(
            "<2I", package, compressed_offset + 16 + index * 8
        )
        result.append((cursor, compressed_size, raw_size))
        cursor += compressed_size
    if cursor != compressed_offset + info[3]:
        raise RuntimeError(f"chunk {chunk_index} block table mismatch")
    return result


def main() -> None:
    original = girl.PACKAGE.read_bytes()
    expanded = bytearray(girl.EXPANDED.read_bytes())
    changed = 0
    for object_offset, object_size, key in girl.object_boundaries():
        first, last = girl.NAMES[key]
        object_data = expanded[object_offset : object_offset + object_size]
        patched_object, _ = girl.patch_localized_object(bytes(object_data), first, last)
        if len(patched_object) > object_size:
            trim = len(patched_object) - object_size
            if patched_object[-trim:] != b"\0" * trim:
                raise RuntimeError(f"object has no alignment room: {key} grew by {trim}")
            patched_object = patched_object[:-trim]
        patched_object += b"\0" * (object_size - len(patched_object))
        if patched_object != bytes(object_data):
            changed += 1
        expanded[object_offset : object_offset + object_size] = patched_object
    if changed != 77:
        raise RuntimeError(f"expected 77 changed objects, found {changed}")
    patched = bytes(expanded)

    infos = [
        package_tools.chunk_info(original, i)
        for i in range(u32(original, package_tools.CHUNK_COUNT_OFFSET))
    ]
    affected: set[tuple[int, int]] = {(girl.CHUNK_INDEX, girl.BLOCK_INDEX)}

    output = bytearray(original)
    compressed_deltas = []
    for chunk_index, block_index in sorted(affected):
        info = infos[chunk_index]
        chunk_start, _, _, _, block_size, _, _ = info
        locations = block_locations(original, chunk_index)
        block_offset, old_size, raw_size = locations[block_index]
        raw_start = chunk_start + block_index * block_size
        raw = patched[raw_start : raw_start + raw_size]
        compressed = girl.compress_lzo(raw)
        if len(compressed) > old_size:
            raise RuntimeError(
                f"compressed block grew: chunk={chunk_index} block={block_index} "
                f"new={len(compressed)} old={old_size}"
            )
        output[block_offset : block_offset + old_size] = compressed + b"\0" * (old_size - len(compressed))
        compressed_deltas.append((chunk_index, block_index, len(compressed), old_size))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_EXPANDED.write_bytes(patched)
    OUT_PACKAGE.write_bytes(output)
    print(f"changed_objects={changed}")
    print(f"affected_blocks={compressed_deltas}")
    print(f"original_size={len(original)} padded_size={len(output)}")
    print(f"output={OUT_PACKAGE}")


if __name__ == "__main__":
    main()
