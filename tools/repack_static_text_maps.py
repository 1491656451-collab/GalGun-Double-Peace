from __future__ import annotations

import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(r"D:\GALGUNVV")
WORK = ROOT / "work"
COMPRESSOR = WORK / "lzo_compress.exe"
TAG = 0x9E2A83C1
TABLE = 0x75
ENTRY_SIZE = 16

MAPS = [
    (
        "title",
        Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\CookedPC\Maps\LoadSwfMovies\LoadSwfMovieTitle_Eng.umap"),
        WORK / "title_static_texts_cht" / "LoadSwfMovieTitle_Eng.umap",
        WORK / "LoadSwfMovieTitle_Eng_static_texts_cht_lzo.umap",
    ),
    (
        "base",
        Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\CookedPC\Maps\LoadSwfMovies\LoadSwfMovieBase_Eng.umap"),
        WORK / "base_static_texts_cht" / "LoadSwfMovieBase_Eng.umap",
        WORK / "LoadSwfMovieBase_Eng_static_texts_cht_lzo.umap",
    ),
]


def u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def put_u32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value)


def compress_block(raw: bytes, directory: Path, index: int) -> bytes:
    source = directory / f"block_{index:03d}.raw"
    destination = directory / f"block_{index:03d}.lzo"
    source.write_bytes(raw)
    subprocess.run(
        [str(COMPRESSOR), str(source), str(destination)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return destination.read_bytes()


def rebuild_chunk(raw: bytes, logical_offset: int, logical_size: int, old_chunk: bytes, temp: Path) -> bytes:
    if u32(old_chunk, 0) != TAG:
        raise RuntimeError("unexpected chunk tag")
    block_size = u32(old_chunk, 4)
    if not block_size:
        raise RuntimeError("invalid chunk block size")
    block_count = (logical_size + block_size - 1) // block_size
    header_size = 16 + block_count * 8
    if header_size > len(old_chunk):
        raise RuntimeError("truncated chunk header")

    compressed_blocks: list[bytes] = []
    compressed_cursor = header_size
    raw_cursor = logical_offset
    remaining = logical_size
    for index in range(block_count):
        expected_size = min(block_size, remaining)
        old_size = u32(old_chunk, 16 + index * 8)
        old_raw_size = u32(old_chunk, 20 + index * 8)
        if old_raw_size != expected_size:
            raise RuntimeError(
                f"raw block size mismatch: expected {expected_size}, got {old_raw_size}"
            )
        if compressed_cursor + old_size > len(old_chunk):
            raise RuntimeError("compressed block exceeds chunk")
        compressed_blocks.append(compress_block(raw[raw_cursor:raw_cursor + expected_size], temp, index))
        compressed_cursor += old_size
        raw_cursor += expected_size
        remaining -= expected_size

    compressed_total = sum(len(item) for item in compressed_blocks)
    rebuilt = bytearray(struct.pack("<4I", TAG, block_size, compressed_total, logical_size))
    for block in compressed_blocks:
        rebuilt.extend(struct.pack("<2I", len(block), min(block_size, logical_size)))
    # The last block can be smaller than block_size.
    for index, block in enumerate(compressed_blocks):
        raw_size = min(block_size, logical_size - index * block_size)
        struct.pack_into("<I", rebuilt, 20 + index * 8, raw_size)
    rebuilt.extend(b"".join(compressed_blocks))
    return bytes(rebuilt)


def repack(label: str, original_path: Path, raw_path: Path, output_path: Path) -> None:
    original = original_path.read_bytes()
    raw = raw_path.read_bytes()
    if u32(original, 0) != TAG or u32(raw, 0) != TAG:
        raise RuntimeError(f"{label}: unexpected package tag")

    entries: list[tuple[int, int, int, int]] = []
    cursor = TABLE
    previous_compressed = 0
    while cursor + ENTRY_SIZE <= len(original):
        logical_offset = u32(original, cursor)
        logical_size = u32(original, cursor + 4)
        compressed_offset = u32(original, cursor + 8)
        compressed_size = u32(original, cursor + 12)
        if not logical_size or compressed_offset <= previous_compressed:
            break
        if compressed_offset >= len(original) or compressed_offset + compressed_size > len(original):
            break
        if logical_offset + logical_size > len(raw):
            break
        entries.append((logical_offset, logical_size, compressed_offset, compressed_size))
        previous_compressed = compressed_offset
        cursor += ENTRY_SIZE

    if not entries or entries[-1][0] + entries[-1][1] != len(raw):
        raise RuntimeError(f"{label}: could not identify all compression chunks")

    chunks: list[bytes] = []
    with tempfile.TemporaryDirectory(prefix=f"{label}_static_lzo_", dir=WORK) as temp_name:
        temp = Path(temp_name)
        for index, (logical_offset, logical_size, compressed_offset, compressed_size) in enumerate(entries):
            old_chunk = original[compressed_offset:compressed_offset + compressed_size]
            chunk = rebuild_chunk(raw, logical_offset, logical_size, old_chunk, temp)
            chunks.append(chunk)
            print(f"{label} chunk {index:02d}: raw=0x{logical_offset:X}/0x{logical_size:X} old={compressed_size} new={len(chunk)}")

    first_compressed = entries[0][2]
    prefix = bytearray(original[:first_compressed])
    output = bytearray(prefix)
    compressed_cursor = first_compressed
    for index, chunk in enumerate(chunks):
        entry = TABLE + index * ENTRY_SIZE
        put_u32(prefix, entry + 8, compressed_cursor)
        put_u32(prefix, entry + 12, len(chunk))
        output.extend(chunk)
        compressed_cursor += len(chunk)
    output[:len(prefix)] = prefix
    output_path.write_bytes(output)
    print(f"{label}: wrote {output_path} ({len(output)} bytes), chunks={len(entries)}")


def main() -> None:
    for label, original, raw, output in MAPS:
        repack(label, original, raw, output)


if __name__ == "__main__":
    main()
