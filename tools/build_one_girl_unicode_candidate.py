from __future__ import annotations

import struct
from pathlib import Path

import rebuild_girl_names as girl
import rebuild_shop_names_package as package_tools


KEY = "02_NIRA_MAOKO"
OUTPUT = Path(r"D:\GALGUNVV\work\one_girl_unicode\GG2Game.u.modified")
EXPANDED_OUTPUT = OUTPUT.with_suffix(".expanded")


def main() -> None:
    original = girl.PACKAGE.read_bytes()
    source_expanded = girl.EXPANDED.read_bytes()
    expanded = bytearray(source_expanded)
    objects = girl.object_boundaries()
    package_info = [
        package_tools.chunk_info(original, i)
        for i in range(package_tools.u32(original, package_tools.CHUNK_COUNT_OFFSET))
    ]
    chunk_start, _, _, _, block_size, _, _ = package_info[girl.CHUNK_INDEX]
    block_start = chunk_start + girl.BLOCK_INDEX * block_size
    block_end = block_start + block_size
    rebuilt_block = bytearray()
    cursor = block_start
    deltas = {}
    for offset, size, key in objects:
        deltas[offset] = 0
        if not (block_start <= offset < block_end):
            continue
        if key == KEY:
            patched, delta = girl.patch_localized_object(source_expanded[offset : offset + size], *girl.NAMES[key])
            rebuilt_block.extend(source_expanded[cursor:offset])
            rebuilt_block.extend(patched)
            deltas[offset] = delta
            cursor = offset + size
    rebuilt_block.extend(source_expanded[cursor:block_end])
    total_delta = sum(deltas.values())
    if total_delta > 0 or len(rebuilt_block) > block_end - block_start:
        raise RuntimeError("candidate does not fit the original block")
    rebuilt_block.extend(b"\0" * (block_end - block_start - len(rebuilt_block)))
    expanded[block_start:block_end] = rebuilt_block

    changed_positions = []
    for index in range(girl.EXPORT_COUNT):
        entry = girl.EXPORT_OFFSET + index * girl.EXPORT_ENTRY_SIZE
        old_size = package_tools.u32(source_expanded, entry + 0x20)
        old_offset = package_tools.u32(source_expanded, entry + 0x24)
        if not (block_start <= old_offset < block_end):
            continue
        shift = sum(delta for offset, delta in deltas.items() if offset < old_offset)
        package_tools.put_u32(expanded, entry + 0x20, old_size + deltas.get(old_offset, 0))
        package_tools.put_u32(expanded, entry + 0x24, old_offset + shift)
        changed_positions.extend((entry + 0x20, entry + 0x24))

    affected = {(girl.CHUNK_INDEX, girl.BLOCK_INDEX)}
    for position in changed_positions:
        for index, info in enumerate(package_info):
            start, _, _, _, size, _, _ = info
            if start <= position < start + info[1]:
                affected.add((index, (position - start) // size))
                break

    package_tools.lzo1x_literal_block = girl.compress_lzo
    rebuilt = original
    for chunk_index, block_index in sorted(affected):
        package_tools.CHUNK_INDEX = chunk_index
        package_tools.BLOCK_INDEX = block_index
        rebuilt = package_tools.rebuild_package(rebuilt, bytes(expanded))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    EXPANDED_OUTPUT.write_bytes(expanded)
    OUTPUT.write_bytes(rebuilt)
    print(f"key={KEY} delta={total_delta} package={len(rebuilt)} output={OUTPUT}")


if __name__ == "__main__":
    main()
