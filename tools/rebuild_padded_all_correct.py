from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, r"D:\GALGUNVV\work")
import rebuild_girl_names as girl
import rebuild_shop_names_package as package_tools


SOURCE_PACKAGE = girl.PACKAGE
SOURCE_EXPANDED = Path(r"D:\GALGUNVV\work\girl_names_padded_package\GG2Game.u.girl_names.padded.expanded")
OUTPUT = Path(r"D:\GALGUNVV\work\girl_names_padded_package\GG2Game.u.girl_names.padded.repacked.modified")


def main() -> None:
    original = SOURCE_PACKAGE.read_bytes()
    expanded = SOURCE_EXPANDED.read_bytes()
    if len(expanded) != girl.EXPANDED.stat().st_size:
        raise RuntimeError("expanded package size changed")
    package_tools.CHUNK_INDEX = girl.CHUNK_INDEX
    package_tools.BLOCK_INDEX = girl.BLOCK_INDEX
    rebuilt = package_tools.rebuild_package(original, expanded)
    OUTPUT.write_bytes(rebuilt)
    print(f"original_size={len(original)} rebuilt_size={len(rebuilt)}")
    print(f"output={OUTPUT}")


if __name__ == "__main__":
    main()
