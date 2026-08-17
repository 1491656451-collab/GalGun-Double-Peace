from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import rebuild_shop_names_package as base


COMPRESSOR = Path(r"D:\GALGUNVV\work\lzo_compress.exe")
base.OUT_PACKAGE = base.WORK_DIR / "GG2Game.u.one_ascii_name.modified"
base.OUT_EXPANDED = base.WORK_DIR / "GG2Game.u.one_ascii_name.expanded"


def compress_lzo1x(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="gg2_one_ascii_", dir=base.WORK_DIR) as temp_dir:
        temp_dir_path = Path(temp_dir)
        raw_path = temp_dir_path / "block.raw"
        compressed_path = temp_dir_path / "block.lzo"
        raw_path.write_bytes(data)
        subprocess.run([str(COMPRESSOR), str(raw_path), str(compressed_path)], check=True)
        return compressed_path.read_bytes()


expanded = bytearray(base.EXPANDED_PACKAGE.read_bytes())
old = b"Red Energy Drink LV1\0"
new = b"Red Energy Drink LX1\0"
pos = expanded.find(old, 0xC85000, 0xC8A000)
if pos < 0:
    raise RuntimeError("target name not found")
expanded[pos:pos + len(old)] = new
base.lzo1x_literal_block = compress_lzo1x
base.OUT_EXPANDED.write_bytes(expanded)
base.OUT_PACKAGE.write_bytes(base.rebuild_package(base.GAME_PACKAGE.read_bytes(), bytes(expanded)))
print(f"position={pos:X} package={base.OUT_PACKAGE.stat().st_size}")
