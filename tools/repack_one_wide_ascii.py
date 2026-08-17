from __future__ import annotations

import subprocess
import struct
import tempfile
from pathlib import Path

import rebuild_shop_names_package as base


COMPRESSOR = Path(r"D:\GALGUNVV\work\lzo_compress.exe")
base.OUT_PACKAGE = base.WORK_DIR / "GG2Game.u.one_wide_ascii.modified"
base.OUT_EXPANDED = base.WORK_DIR / "GG2Game.u.one_wide_ascii.expanded"
base.SHOP_OBJECT_END = 0xC88EDB


def compress_lzo1x(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="gg2_one_wide_", dir=base.WORK_DIR) as temp_dir:
        temp_dir_path = Path(temp_dir)
        raw_path = temp_dir_path / "block.raw"
        compressed_path = temp_dir_path / "block.lzo"
        raw_path.write_bytes(data)
        subprocess.run([str(COMPRESSOR), str(raw_path), str(compressed_path)], check=True)
        return compressed_path.read_bytes()


expanded = base.EXPANDED_PACKAGE.read_bytes()
needle = b"Red Energy Drink LV1\0"
pos = expanded.find(needle, 0xC85000, 0xC8A000)
if pos < 4:
    raise RuntimeError("target name not found")
wide = struct.pack("<i", -len("Red Energy Drink LV1") - 1)
wide += "Red Energy Drink LV1".encode("utf-16-le") + b"\0\0"
start = pos - 4
old_len = 4 + len(needle)
delta = len(wide) - old_len
rebuilt = bytearray()
rebuilt.extend(expanded[:start])
rebuilt.extend(wide)
rebuilt.extend(expanded[start + old_len:base.SHOP_OBJECT_END])
rebuilt.extend(b"\0" * (-delta))
rebuilt.extend(expanded[base.SHOP_OBJECT_END:])
if len(rebuilt) != len(expanded):
    raise RuntimeError("expanded size changed")
base.lzo1x_literal_block = compress_lzo1x
base.OUT_EXPANDED.write_bytes(rebuilt)
base.OUT_PACKAGE.write_bytes(base.rebuild_package(base.GAME_PACKAGE.read_bytes(), bytes(rebuilt)))
print(f"position={pos:X} delta={delta} package={base.OUT_PACKAGE.stat().st_size}")
