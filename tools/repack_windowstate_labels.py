from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import rebuild_shop_names_package as base


ROOT = Path(r"D:\GALGUNVV")
WORK = ROOT / "work"
COMPRESSOR = WORK / "lzo_compress.exe"
PACKAGE = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\CookedPC\GG2Game.u")
EXPANDED = WORK / "windowstate_labels_cht_expanded" / "GG2Game.u"
OUTPUT = WORK / "windowstate_labels_cht_lzo" / "GG2Game.u"

PAYLOAD_START = 0xA56CBD3
PAYLOAD_END = PAYLOAD_START + 1024 * 512


def compress_lzo(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="windowstate_lzo_", dir=WORK) as temp:
        temp_dir = Path(temp)
        raw = temp_dir / "block.raw"
        compressed = temp_dir / "block.lzo"
        raw.write_bytes(data)
        subprocess.run([str(COMPRESSOR), str(raw), str(compressed)], check=True)
        return compressed.read_bytes()


def affected_blocks(package: bytes) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    count = base.u32(package, base.CHUNK_COUNT_OFFSET)
    infos = [base.chunk_info(package, index) for index in range(count)]
    for chunk_index, info in enumerate(infos):
        logical_offset, logical_size, *_rest = info
        block_size = info[4]
        first = max(PAYLOAD_START, logical_offset)
        last = min(PAYLOAD_END, logical_offset + logical_size)
        if first < last:
            first_block = (first - logical_offset) // block_size
            last_block = (last - 1 - logical_offset) // block_size
            for block_index in range(first_block, last_block + 1):
                result.add((chunk_index, block_index))
    return result


def main() -> None:
    original = PACKAGE.read_bytes()
    patched = EXPANDED.read_bytes()
    if len(patched) != 182922998:
        raise RuntimeError(f"unexpected expanded package size: {len(patched)}")
    if original == patched:
        raise RuntimeError("candidate expanded package is unchanged")

    base.lzo1x_literal_block = compress_lzo
    rebuilt = original
    blocks = sorted(affected_blocks(original))
    if not blocks:
        raise RuntimeError("texture payload is outside package compression chunks")
    print("affected_blocks", blocks)
    for chunk_index, block_index in blocks:
        base.CHUNK_INDEX = chunk_index
        base.BLOCK_INDEX = block_index
        rebuilt = base.rebuild_package(rebuilt, patched)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(rebuilt)
    print(f"wrote {OUTPUT} ({len(rebuilt)} bytes)")


if __name__ == "__main__":
    main()
