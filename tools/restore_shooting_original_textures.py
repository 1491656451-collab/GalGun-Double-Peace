from __future__ import annotations

import struct
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from translate_title_buttons import compress_dxt5


ROOT = Path(r"D:\GALGUNVV")
WORK = ROOT / "work"
PACKAGE = Path(
    r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\CookedPC\Maps\LoadSwfMovies\LoadSwfMovieShooting_Eng.umap"
)
RAW = WORK / "shooting_decompressed" / "LoadSwfMovieShooting_Eng.umap"
EXPORT = WORK / "shooting_assets_export" / "LoadSwfMovieShooting_Eng" / "Texture2D"
COMPRESSOR = WORK / "lzo_compress.exe"
OUTPUT = WORK / "LoadSwfMovieShooting_Eng_restored_original_lzo.umap"

TABLE_OFFSET = 0x75
ENTRY_SIZE = 16
TAG = 0x9E2A83C1
BLOCK_HEADER_SIZE = 16
BLOCK_ENTRY_SIZE = 8

RESTORES = {
    0x6A025: "ScreenContinue_Eng_I18.png",
    0xB73AF: "ScreenContinue_Eng_IB.png",
}


def u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def put_u32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value)


def package_entries(package: bytes, raw_size: int) -> list[tuple[int, int, int, int]]:
    entries = []
    cursor = TABLE_OFFSET
    previous_compressed = 0
    while cursor + ENTRY_SIZE <= len(package):
        logical_offset, logical_size, compressed_offset, compressed_size = struct.unpack_from(
            "<4I", package, cursor
        )
        if not logical_size or compressed_offset <= previous_compressed:
            break
        if compressed_offset + compressed_size > len(package):
            break
        if logical_offset + logical_size > raw_size:
            break
        entries.append((logical_offset, logical_size, compressed_offset, compressed_size))
        previous_compressed = compressed_offset
        cursor += ENTRY_SIZE
    if not entries or entries[-1][0] + entries[-1][1] != raw_size:
        raise RuntimeError("could not identify all compression chunks")
    return entries


def block_ranges(package: bytes, entry: tuple[int, int, int, int]) -> list[tuple[int, int, int]]:
    _, logical_size, compressed_offset, compressed_size = entry
    if u32(package, compressed_offset) != TAG:
        raise RuntimeError("unexpected compression tag")
    block_size = u32(package, compressed_offset + 4)
    block_count = (logical_size + block_size - 1) // block_size
    header_size = BLOCK_HEADER_SIZE + block_count * BLOCK_ENTRY_SIZE
    cursor = compressed_offset + header_size
    blocks = []
    for index in range(block_count):
        compressed_size_i, raw_size_i = struct.unpack_from(
            "<2I", package, compressed_offset + BLOCK_HEADER_SIZE + index * BLOCK_ENTRY_SIZE
        )
        blocks.append((cursor, compressed_size_i, raw_size_i))
        cursor += compressed_size_i
    if cursor != compressed_offset + compressed_size:
        raise RuntimeError("compression block layout mismatch")
    return blocks


def compress_block(raw: bytes, directory: Path, index: int) -> bytes:
    source = directory / f"block_{index:03d}.raw"
    destination = directory / f"block_{index:03d}.lzo"
    source.write_bytes(raw)
    subprocess.run([str(COMPRESSOR), str(source), str(destination)], check=True)
    return destination.read_bytes()


def main() -> None:
    package = PACKAGE.read_bytes()
    raw = bytearray(RAW.read_bytes())
    if u32(package, 0) != TAG or u32(raw, 0) != TAG:
        raise RuntimeError("unexpected package tag")

    changed_ranges = []
    for offset, filename in RESTORES.items():
        image = Image.open(EXPORT / filename).convert("RGBA")
        payload = compress_dxt5(image)
        if len(payload) != 512 * 128:
            raise RuntimeError(f"{filename}: unexpected DXT5 payload size")
        if raw[offset : offset + len(payload)] == payload:
            raise RuntimeError(f"{filename}: raw package already contains the original texture")
        raw[offset : offset + len(payload)] = payload
        changed_ranges.append((offset, offset + len(payload)))

    entries = package_entries(package, len(raw))
    changed_blocks: set[tuple[int, int]] = set()
    for chunk_index, entry in enumerate(entries):
        logical_offset, logical_size, _, _ = entry
        block_size = u32(package, entry[2] + 4)
        for start, end in changed_ranges:
            overlap_start = max(start, logical_offset)
            overlap_end = min(end, logical_offset + logical_size)
            if overlap_start < overlap_end:
                first = (overlap_start - logical_offset) // block_size
                last = (overlap_end - 1 - logical_offset) // block_size
                changed_blocks.update((chunk_index, i) for i in range(first, last + 1))

    rebuilt = bytearray(package[: entries[0][2]])
    new_entries = []
    with tempfile.TemporaryDirectory(prefix="restore_shooting_", dir=WORK) as temp_name:
        temp = Path(temp_name)
        for chunk_index, entry in enumerate(entries):
            logical_offset, logical_size, _, old_compressed_size = entry
            old_blocks = block_ranges(package, entry)
            block_size = u32(package, entry[2] + 4)
            header_size = BLOCK_HEADER_SIZE + len(old_blocks) * BLOCK_ENTRY_SIZE
            header = bytearray(package[entry[2] : entry[2] + header_size])
            blocks = []
            for block_index, (block_offset, old_size, raw_size) in enumerate(old_blocks):
                raw_start = logical_offset + block_index * block_size
                block_raw = bytes(raw[raw_start : raw_start + raw_size])
                if (chunk_index, block_index) in changed_blocks:
                    compressed = compress_block(block_raw, temp, block_index)
                    put_u32(header, BLOCK_HEADER_SIZE + block_index * BLOCK_ENTRY_SIZE, len(compressed))
                else:
                    compressed = package[block_offset : block_offset + old_size]
                blocks.append(compressed)
            compressed_total = sum(len(item) for item in blocks)
            put_u32(header, 8, compressed_total)
            chunk = bytes(header) + b"".join(blocks)
            new_offset = len(rebuilt)
            rebuilt.extend(chunk)
            new_entries.append((logical_offset, logical_size, new_offset, len(chunk)))

    for index, entry in enumerate(new_entries):
        table = TABLE_OFFSET + index * ENTRY_SIZE
        for field, value in enumerate(entry):
            put_u32(rebuilt, table + field * 4, value)

    OUTPUT.write_bytes(rebuilt)
    print(f"restored blocks: {sorted(changed_blocks)}")
    print(f"output: {OUTPUT} ({len(rebuilt)} bytes)")


if __name__ == "__main__":
    main()
