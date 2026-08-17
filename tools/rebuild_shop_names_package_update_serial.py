from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import rebuild_shop_names_package as base


COMPRESSOR = Path(r"D:\GALGUNVV\work\lzo_compress.exe")
SERIAL_SIZE_OFFSET = 0x40FB8E
base.OUT_PACKAGE = base.WORK_DIR / "GG2Game.u.shopnames.update_serial.modified"
base.OUT_EXPANDED = base.WORK_DIR / "GG2Game.u.shopnames.update_serial.expanded"
base.SHOP_OBJECT_END = 0xC88EDB


def compress_lzo1x(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="gg2_serial_", dir=base.WORK_DIR) as temp_dir:
        temp_dir_path = Path(temp_dir)
        raw_path = temp_dir_path / "block.raw"
        compressed_path = temp_dir_path / "block.lzo"
        raw_path.write_bytes(data)
        subprocess.run([str(COMPRESSOR), str(raw_path), str(compressed_path)], check=True)
        return compressed_path.read_bytes()


old_patch = base.patch_expanded


def patch_expanded_and_serial(expanded: bytes, names: list[str]) -> tuple[bytes, int]:
    patched, delta = old_patch(expanded, names)
    patched_buffer = bytearray(patched)
    base.put_u32(
        patched_buffer,
        SERIAL_SIZE_OFFSET,
        base.u32(patched_buffer, SERIAL_SIZE_OFFSET) + delta,
    )
    return bytes(patched_buffer), delta


base.patch_expanded = patch_expanded_and_serial
base.lzo1x_literal_block = compress_lzo1x
base.main()
