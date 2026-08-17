from __future__ import annotations

import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(r"D:\GALGUNVV")
ORIGINAL_MAP = Path(
    r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\CookedPC\Maps\LoadSwfMovies\LoadSwfMovieTitle_Eng.umap"
)
RAW_MAP = ROOT / "work" / "LoadSwfMovieTitle_Eng_cht.umap"
OUT_MAP = ROOT / "work" / "LoadSwfMovieTitle_Eng_cht_lzo.umap"
LZO_COMPRESSOR = ROOT / "work" / "lzo_compress.exe"

CHUNK_TABLE = 0x75
CHUNK_COUNT = 19
CHUNK_ENTRY_SIZE = 16
PACKAGE_HEADER_SIZE = 0x3B36
PACKAGE_TAG = 0x9E2A83C1


def u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def put_u32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value)


def compress_block(source: bytes, temp_dir: Path, index: int) -> bytes:
    input_path = temp_dir / f"block_{index:03d}.raw"
    output_path = temp_dir / f"block_{index:03d}.lzo"
    input_path.write_bytes(source)
    subprocess.run(
        [str(LZO_COMPRESSOR), str(input_path), str(output_path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return output_path.read_bytes()


def rebuild_chunk(raw: bytes, logical_offset: int, logical_size: int, old_chunk: bytes) -> bytes:
    if logical_offset + logical_size > len(raw):
        raise RuntimeError("logical chunk exceeds raw map")
    if u32(old_chunk, 0) != PACKAGE_TAG:
        raise RuntimeError("unexpected LZO chunk tag")
    block_size = u32(old_chunk, 4)
    if block_size == 0:
        raise RuntimeError("invalid LZO block size")
    block_count = (logical_size + block_size - 1) // block_size
    old_header_size = 16 + block_count * 8
    if old_header_size > len(old_chunk):
        raise RuntimeError("old LZO chunk header is truncated")

    blocks: list[tuple[bytes, int]] = []
    compressed_cursor = old_header_size
    raw_cursor = logical_offset
    remaining = logical_size
    with tempfile.TemporaryDirectory(prefix="title_lzo_", dir=ROOT / "work") as temp_name:
        temp_dir = Path(temp_name)
        for index in range(block_count):
            expected_raw_size = min(block_size, remaining)
            old_compressed_size = u32(old_chunk, 16 + index * 8)
            old_raw_size = u32(old_chunk, 20 + index * 8)
            if old_raw_size != expected_raw_size:
                raise RuntimeError(
                    f"block {index}: expected raw size {expected_raw_size}, got {old_raw_size}"
                )
            if compressed_cursor + old_compressed_size > len(old_chunk):
                raise RuntimeError("old LZO block exceeds chunk")
            compressed = compress_block(raw[raw_cursor:raw_cursor + expected_raw_size], temp_dir, index)
            blocks.append((compressed, expected_raw_size))
            compressed_cursor += old_compressed_size
            raw_cursor += expected_raw_size
            remaining -= expected_raw_size

    header_size = 16 + block_count * 8
    compressed_total = sum(len(block) for block, _ in blocks)
    chunk = bytearray()
    chunk.extend(struct.pack("<4I", PACKAGE_TAG, block_size, compressed_total, logical_size))
    for compressed, raw_size in blocks:
        chunk.extend(struct.pack("<2I", len(compressed), raw_size))
    for compressed, _ in blocks:
        chunk.extend(compressed)
    if len(chunk) != header_size + compressed_total:
        raise RuntimeError("rebuilt LZO chunk size mismatch")
    return bytes(chunk)


def main() -> None:
    original = ORIGINAL_MAP.read_bytes()
    raw = RAW_MAP.read_bytes()
    if u32(original, 0) != PACKAGE_TAG or u32(raw, 0) != PACKAGE_TAG:
        raise RuntimeError("unexpected package tag")
    if u32(original, 8) != PACKAGE_HEADER_SIZE:
        raise RuntimeError("unexpected package header size")

    first_compressed_offset = u32(original, CHUNK_TABLE + 8)
    if first_compressed_offset == 0:
        raise RuntimeError("unexpected first compressed offset")

    chunks: list[tuple[int, int, bytes]] = []
    with tempfile.TemporaryDirectory(prefix="title_repack_", dir=ROOT / "work"):
        for index in range(CHUNK_COUNT):
            entry = CHUNK_TABLE + index * CHUNK_ENTRY_SIZE
            logical_offset = u32(original, entry)
            logical_size = u32(original, entry + 4)
            compressed_offset = u32(original, entry + 8)
            compressed_size = u32(original, entry + 12)
            old_chunk = original[compressed_offset:compressed_offset + compressed_size]
            rebuilt = rebuild_chunk(raw, logical_offset, logical_size, old_chunk)
            chunks.append((logical_offset, logical_size, rebuilt))
            print(
                f"chunk {index:02d}: raw=0x{logical_offset:X}/0x{logical_size:X} "
                f"old=0x{compressed_size:X} new=0x{len(rebuilt):X}"
            )

    prefix = bytearray(original[:first_compressed_offset])
    output = bytearray(prefix)
    compressed_cursor = first_compressed_offset
    for index, (logical_offset, logical_size, chunk) in enumerate(chunks):
        entry = CHUNK_TABLE + index * CHUNK_ENTRY_SIZE
        put_u32(prefix, entry, logical_offset)
        put_u32(prefix, entry + 4, logical_size)
        put_u32(prefix, entry + 8, compressed_cursor)
        put_u32(prefix, entry + 12, len(chunk))
        output.extend(chunk)
        compressed_cursor += len(chunk)

    output[:len(prefix)] = prefix
    OUT_MAP.write_bytes(output)
    print(f"wrote {OUT_MAP} ({len(output)} bytes)")


if __name__ == "__main__":
    main()
