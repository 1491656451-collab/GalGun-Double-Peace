from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import rebuild_shop_names_package as base


COMPRESSOR = Path(r"D:\GALGUNVV\work\lzo_compress_15.exe")
base.OUT_PACKAGE = base.WORK_DIR / "GG2Game.u.shopnames.lzo15.modified"
base.OUT_EXPANDED = base.WORK_DIR / "GG2Game.u.shopnames.lzo15.expanded"


def compress_lzo1x(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="gg2_lzo15_", dir=base.WORK_DIR) as temp_dir:
        temp_dir_path = Path(temp_dir)
        raw_path = temp_dir_path / "block.raw"
        compressed_path = temp_dir_path / "block.lzo"
        raw_path.write_bytes(data)
        subprocess.run([str(COMPRESSOR), str(raw_path), str(compressed_path)], check=True)
        return compressed_path.read_bytes()


base.lzo1x_literal_block = compress_lzo1x
base.main()
