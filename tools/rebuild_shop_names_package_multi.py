from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import rebuild_shop_names_package as base


COMPRESSOR = Path(r"D:\GALGUNVV\work\lzo_compress.exe")
SERIAL_SIZE_OFFSET = 0x40FB8E
base.OUT_PACKAGE = base.WORK_DIR / "GG2Game.u.shopnames.multi.modified"
base.OUT_EXPANDED = base.WORK_DIR / "GG2Game.u.shopnames.multi.expanded"
base.SHOP_OBJECT_END = 0xC88EDB


def compress_lzo1x(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="gg2_multi_", dir=base.WORK_DIR) as temp_dir:
        temp_dir_path = Path(temp_dir)
        raw_path = temp_dir_path / "block.raw"
        compressed_path = temp_dir_path / "block.lzo"
        raw_path.write_bytes(data)
        subprocess.run([str(COMPRESSOR), str(raw_path), str(compressed_path)], check=True)
        return compressed_path.read_bytes()


original = base.GAME_PACKAGE.read_bytes()
expanded = base.EXPANDED_PACKAGE.read_bytes()
names = base.target_names()
patched_expanded, text_delta = base.patch_expanded(expanded, names)
patched_buffer = bytearray(patched_expanded)
base.put_u32(
    patched_buffer,
    SERIAL_SIZE_OFFSET,
    base.u32(patched_buffer, SERIAL_SIZE_OFFSET) + text_delta,
)
patched_expanded = bytes(patched_buffer)

base.lzo1x_literal_block = compress_lzo1x
base.CHUNK_INDEX = 8
base.BLOCK_INDEX = 2
repacked = base.rebuild_package(original, patched_expanded)
base.CHUNK_INDEX = 0
base.BLOCK_INDEX = 32
repacked = base.rebuild_package(repacked, patched_expanded)

base.OUT_EXPANDED.write_bytes(patched_expanded)
base.OUT_PACKAGE.write_bytes(repacked)
print(f"names={len(names)} text_delta={text_delta}")
print(f"original={len(original)} rebuilt={len(repacked)}")
print(f"serial={base.u32(patched_expanded, SERIAL_SIZE_OFFSET)}")
print(f"out={base.OUT_PACKAGE}")
