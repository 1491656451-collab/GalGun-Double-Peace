from __future__ import annotations

import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(r"D:\GALGUNVV")
GAME_ROOT = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game")
PACKAGE = GAME_ROOT / "CookedPC" / "GG2Game.u"
EXPANDED = ROOT / "work" / "current_package_decompressed_test" / "GG2Game.u"
GFX = ROOT / "work" / "WindowPause_cht_test_frame1.gfx"
COMPRESSOR = ROOT / "work" / "lzo_compress.exe"
OUT_DIR = ROOT / "work" / "pause_gfx_package"
OUT_EXPANDED = OUT_DIR / "GG2Game.u.pause_cht.expanded"
OUT_PACKAGE = OUT_DIR / "GG2Game.u.pause_cht.modified"

TABLE_OFFSET = 0x75
CHUNK_COUNT_OFFSET = 0x71
CHUNK_ENTRY_SIZE = 16
PACKAGE_TAG = 0x9E2A83C1
BLOCK_HEADER_SIZE = 16
BLOCK_ENTRY_SIZE = 8
BLOCK_SIZE = 131072

EXPORT_OFFSET = 0x138C82
EXPORT_COUNT = 56902
EXPORT_ENTRY_SIZE = 0x44
EXPORT_SERIAL_SIZE = 0x18
EXPORT_SERIAL_OFFSET = 0x1C

WINDOW_PAUSE_OBJECT = 0x49E6B81
WINDOW_PAUSE_GFX_OFFSET = 0x106
OLD_GFX_SIZE = 12324


def u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def put_u32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value)


def chunk_info(data: bytes, index: int) -> tuple[int, int, int, int, int, int, int]:
    entry = TABLE_OFFSET + index * CHUNK_ENTRY_SIZE
    uncompressed_offset, uncompressed_size, compressed_offset, compressed_size = struct.unpack_from(
        "<4I", data, entry
    )
    tag, block_size, compressed_total, uncompressed_total = struct.unpack_from(
        "<4I", data, compressed_offset
    )
    if tag != PACKAGE_TAG or block_size != BLOCK_SIZE or uncompressed_size != uncompressed_total:
        raise RuntimeError(f"invalid chunk {index}")
    block_count = (uncompressed_total + block_size - 1) // block_size
    header_size = BLOCK_HEADER_SIZE + block_count * BLOCK_ENTRY_SIZE
    if compressed_total + header_size != compressed_size:
        raise RuntimeError(f"chunk {index} size mismatch")
    return (
        uncompressed_offset,
        uncompressed_size,
        compressed_offset,
        compressed_size,
        block_size,
        block_count,
        header_size,
    )


def block_ranges(package: bytes, info: tuple[int, int, int, int, int, int, int]) -> list[tuple[int, int, int]]:
    _, _, compressed_offset, _, _, block_count, header_size = info
    cursor = compressed_offset + header_size
    result = []
    for index in range(block_count):
        compressed_size, raw_size = struct.unpack_from(
            "<2I", package, compressed_offset + BLOCK_HEADER_SIZE + index * BLOCK_ENTRY_SIZE
        )
        result.append((cursor, compressed_size, raw_size))
        cursor += compressed_size
    if cursor != compressed_offset + info[3]:
        raise RuntimeError("compressed block layout mismatch")
    return result


def compress_block(raw: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="pause_gfx_", dir=OUT_DIR) as temp:
        temp_dir = Path(temp)
        raw_path = temp_dir / "block.raw"
        compressed_path = temp_dir / "block.lzo"
        raw_path.write_bytes(raw)
        subprocess.run([str(COMPRESSOR), str(raw_path), str(compressed_path)], check=True)
        return compressed_path.read_bytes()


def patch_expanded(original: bytes, new_gfx: bytes, infos: list[tuple[int, int, int, int, int, int, int]]) -> tuple[bytes, int, int, list[int]]:
    gfx_start = WINDOW_PAUSE_OBJECT + WINDOW_PAUSE_GFX_OFFSET
    if original[gfx_start : gfx_start + 4] != b"GFX\x0c":
        raise RuntimeError(f"WindowPause GFX marker not found at {gfx_start:#x}")
    if original[gfx_start : gfx_start + OLD_GFX_SIZE] != (ROOT / "work" / "windowpause_export" / "GG2Game" / "SwfMovie" / "WindowPause.gfx").read_bytes():
        raise RuntimeError("expanded package does not contain the expected original WindowPause.gfx")

    old_object_size = next_offset = None
    object_index = None
    for index in range(EXPORT_COUNT):
        entry = EXPORT_OFFSET + index * EXPORT_ENTRY_SIZE
        offset = u32(original, entry + EXPORT_SERIAL_OFFSET)
        if offset == WINDOW_PAUSE_OBJECT:
            old_object_size = u32(original, entry + EXPORT_SERIAL_SIZE)
            object_index = index
            break
    if old_object_size is None or object_index is None:
        raise RuntimeError("WindowPause export was not found")
    old_object_end = WINDOW_PAUSE_OBJECT + old_object_size
    if old_object_size != 0x318A:
        raise RuntimeError(f"unexpected WindowPause serial size: {old_object_size:#x}")

    delta = len(new_gfx) - OLD_GFX_SIZE
    patched = bytearray(original[:gfx_start] + new_gfx + original[gfx_start + OLD_GFX_SIZE :])
    modified_positions: list[int] = []
    for index in range(EXPORT_COUNT):
        entry = EXPORT_OFFSET + index * EXPORT_ENTRY_SIZE
        old_offset = u32(original, entry + EXPORT_SERIAL_OFFSET)
        old_size = u32(original, entry + EXPORT_SERIAL_SIZE)
        if index == object_index:
            put_u32(patched, entry + EXPORT_SERIAL_SIZE, old_size + delta)
            modified_positions.append(entry + EXPORT_SERIAL_SIZE)
        elif old_object_end <= old_offset < len(original):
            put_u32(patched, entry + EXPORT_SERIAL_OFFSET, old_offset + delta)
            modified_positions.append(entry + EXPORT_SERIAL_OFFSET)
    return bytes(patched), delta, object_index, modified_positions


def rebuild_package(
    original: bytes,
    expanded: bytes,
    delta: int,
    infos: list[tuple[int, int, int, int, int, int, int]],
    modified_positions: list[int],
) -> bytes:
    target_chunk = None
    gfx_start = WINDOW_PAUSE_OBJECT + WINDOW_PAUSE_GFX_OFFSET
    for index, info in enumerate(infos):
        start, size = info[0], info[1]
        if start <= gfx_start < start + size:
            target_chunk = index
            break
    if target_chunk is None:
        raise RuntimeError("GFX is outside all package chunks")
    target_block = (gfx_start - infos[target_chunk][0]) // BLOCK_SIZE
    changed_blocks = {(target_chunk, block) for block in range(target_block, infos[target_chunk][5])}
    for position in modified_positions:
        for index, info in enumerate(infos):
            start, size = info[0], info[1]
            if start <= position < start + size:
                changed_blocks.add((index, (position - start) // BLOCK_SIZE))
                break
        else:
            raise RuntimeError(f"modified export position outside chunks: {position:#x}")

    first_compressed = infos[0][2]
    rebuilt = bytearray(original[:first_compressed])
    new_chunk_offsets: list[tuple[int, int, int, int]] = []
    compressed_shift = 0

    for index, info in enumerate(infos):
        old_start, old_size, old_compressed_offset, old_compressed_size, block_size, block_count, header_size = info
        old_blocks = block_ranges(original, info)
        new_start = old_start + (delta if old_start >= WINDOW_PAUSE_OBJECT + infos[target_chunk][1] else 0)
        new_size = old_size + (delta if index == target_chunk else 0)
        chunk_header = bytearray(original[old_compressed_offset : old_compressed_offset + header_size])
        blocks: list[bytes] = []
        changed_compressed_delta = 0
        for block_index, (block_offset, old_compressed_size_i, raw_size) in enumerate(old_blocks):
            raw_start = new_start + block_index * block_size
            raw_end = min(new_start + new_size, raw_start + block_size)
            raw = expanded[raw_start:raw_end]
            expected_raw_size = min(block_size, new_size - block_index * block_size)
            if len(raw) != expected_raw_size:
                raise RuntimeError(f"chunk {index} block {block_index} raw size mismatch")
            changed = (index, block_index) in changed_blocks
            if changed:
                compressed = compress_block(raw)
                changed_compressed_delta += len(compressed) - old_compressed_size_i
            else:
                compressed = original[block_offset : block_offset + old_compressed_size_i]
            blocks.append(compressed)
            if changed:
                put_u32(chunk_header, BLOCK_HEADER_SIZE + block_index * BLOCK_ENTRY_SIZE, len(compressed))
                put_u32(chunk_header, BLOCK_HEADER_SIZE + block_index * BLOCK_ENTRY_SIZE + 4, len(raw))

        if changed_compressed_delta:
            put_u32(chunk_header, 8, u32(chunk_header, 8) + changed_compressed_delta)
        if index == target_chunk:
            put_u32(chunk_header, 12, new_size)
        chunk_data = chunk_header + b"".join(blocks)
        if len(chunk_data) != old_compressed_size + changed_compressed_delta:
            raise RuntimeError(f"chunk {index} rebuilt size mismatch")
        new_compressed_offset = len(rebuilt)
        rebuilt.extend(chunk_data)
        new_compressed_size = len(chunk_data)
        new_chunk_offsets.append((new_start, new_size, new_compressed_offset, new_compressed_size))
        compressed_shift += changed_compressed_delta

    # The package table is before the compressed chunks, so its fields can be
    # updated after all chunks have been laid out.
    for index, (new_start, new_size, new_compressed_offset, new_compressed_size) in enumerate(new_chunk_offsets):
        entry = TABLE_OFFSET + index * CHUNK_ENTRY_SIZE
        put_u32(rebuilt, entry, new_start)
        put_u32(rebuilt, entry + 4, new_size)
        put_u32(rebuilt, entry + 8, new_compressed_offset)
        put_u32(rebuilt, entry + 12, new_compressed_size)

    if len(rebuilt) != len(original) + compressed_shift:
        raise RuntimeError("final package size mismatch")
    return bytes(rebuilt)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    original_package = PACKAGE.read_bytes()
    original_expanded = EXPANDED.read_bytes()
    new_gfx = GFX.read_bytes()
    infos = [chunk_info(original_package, index) for index in range(u32(original_package, CHUNK_COUNT_OFFSET))]
    patched_expanded, delta, export_index, modified_positions = patch_expanded(original_expanded, new_gfx, infos)
    rebuilt_package = rebuild_package(original_package, patched_expanded, delta, infos, modified_positions)
    OUT_EXPANDED.write_bytes(patched_expanded)
    OUT_PACKAGE.write_bytes(rebuilt_package)
    print(f"gfx={len(new_gfx)} delta={delta} export={export_index}")
    print(f"expanded={len(patched_expanded)} package={len(rebuilt_package)}")
    print(f"out={OUT_PACKAGE}")


if __name__ == "__main__":
    main()
