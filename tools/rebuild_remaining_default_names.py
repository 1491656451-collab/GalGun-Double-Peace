from __future__ import annotations

import struct
import tempfile
from pathlib import Path

import rebuild_shop_names_package as base


COMPRESSOR = Path(r"D:\GALGUNVV\work\lzo_compress.exe")
WORK_DIR = Path(r"D:\GALGUNVV\work\shop_package_rebuild")
BASE_PACKAGE = Path(
    r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\CookedPC\GG2Game.u"
)
BASE_EXPANDED = WORK_DIR / "GG2Game.u.shopnames.multi.expanded"
OUT_PACKAGE = WORK_DIR / "GG2Game.u.remaining_names.modified"
OUT_EXPANDED = WORK_DIR / "GG2Game.u.remaining_names.expanded"

CHARA_SERIAL_SIZE_OFFSET = 0x3FF2FE
SHOP_SERIAL_SIZE_OFFSET = 0x40FB8E
CHARA_OBJECT_END = 0xC68ACF
SHOP_OBJECT_END = 0xC88EDB

REPLACEMENTS = {
    "Bookworm": "書呆子",
    "Jock": "運動派",
    "Fashionista": "時尚達人",
    "Pervert": "變態",
    "Nothing Special": "平平無奇",
    "Gentleman": "紳士",
    "Hentai Fiend": "色鬼",
    "TFG (That Friggin' Guy)": "那個厲害傢伙",
    "Welcome to the Academy Store!": "歡迎來到學院商店！",
}

GFX_REPLACEMENTS = {
    "Return to the previous screen?": "返回上一頁嗎？",
    "This page to Default": "恢復預設值",
    "Apply All": "全套用",
}

GFX_REGION = (0x49C5000, 0x49D0000)


def u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def put_u32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value)


def patch_expanded(expanded: bytes) -> tuple[bytes, int, list[tuple[str, int]], list[int]]:
    replacements: list[tuple[int, int, bytes, str, int, int]] = []
    counts: list[tuple[str, int]] = []
    for source, target in REPLACEMENTS.items():
        start = 0xC68000 if source != "Welcome to the Academy Store!" else 0xC85000
        end = 0xC6A000 if source != "Welcome to the Academy Store!" else 0xC86000
        needle = source.encode("ascii") + b"\0"
        positions = []
        cursor = start
        while True:
            pos = expanded.find(needle, cursor, end)
            if pos < 0:
                break
            positions.append(pos)
            cursor = pos + len(needle)
        counts.append((source, len(positions)))
        if len(positions) != 1:
            raise RuntimeError(f"expected one {source!r}, found {len(positions)}")
        pos = positions[0]
        old_size = 4 + len(needle)
        encoded = target.encode("utf-16-le") + b"\0\0"
        replacement = struct.pack("<i", -(len(target) + 1)) + encoded
        boundary = CHARA_OBJECT_END if source != "Welcome to the Academy Store!" else SHOP_OBJECT_END
        replacements.append((pos - 4, old_size, replacement, source, pos, boundary))

    replacements.sort()
    chara = [item for item in replacements if item[5] == CHARA_OBJECT_END]
    shop = [item for item in replacements if item[5] == SHOP_OBJECT_END]
    rebuilt = bytearray(expanded[:0])
    cursor = 0
    deltas: dict[int, int] = {}
    for group_start, group_end, group in (
        (0, CHARA_OBJECT_END, chara),
        (CHARA_OBJECT_END, SHOP_OBJECT_END, shop),
    ):
        rebuilt.extend(expanded[cursor:group_start])
        local = group_start
        group_delta = 0
        for start, old_size, replacement, _, _, _ in group:
            rebuilt.extend(expanded[local:start])
            rebuilt.extend(replacement)
            local = start + old_size
            group_delta += len(replacement) - old_size
        rebuilt.extend(expanded[local:group_end])
        rebuilt.extend(b"\0" * (-group_delta))
        deltas[group_end] = group_delta
        cursor = group_end
    rebuilt.extend(expanded[cursor:])
    if len(rebuilt) != len(expanded):
        raise RuntimeError("expanded package size changed")

    buffer = bytearray(rebuilt)
    put_u32(buffer, CHARA_SERIAL_SIZE_OFFSET, u32(buffer, CHARA_SERIAL_SIZE_OFFSET) + deltas[CHARA_OBJECT_END])
    put_u32(buffer, SHOP_SERIAL_SIZE_OFFSET, u32(buffer, SHOP_SERIAL_SIZE_OFFSET) + deltas[SHOP_OBJECT_END])
    serial_positions = [CHARA_SERIAL_SIZE_OFFSET, SHOP_SERIAL_SIZE_OFFSET]
    text_positions = [item[4] for item in replacements]
    return bytes(buffer), sum(deltas.values()), counts, serial_positions + text_positions


def patch_gfx(expanded: bytes) -> tuple[bytes, list[int]]:
    buffer = bytearray(expanded)
    positions: list[int] = []
    start, end = GFX_REGION
    for source, target in GFX_REPLACEMENTS.items():
        needle = source.encode("utf-8") + b"\0"
        pos = expanded.find(needle, start, end)
        if pos < 0:
            raise RuntimeError(f"missing GFX string: {source}")
        replacement = target.encode("utf-8")
        if len(replacement) > len(source.encode("utf-8")):
            raise RuntimeError(f"GFX replacement is longer: {source}")
        replacement += b" " * (len(source.encode("utf-8")) - len(replacement))
        buffer[pos:pos + len(replacement)] = replacement
        positions.append(pos)
    return bytes(buffer), positions


def compress_lzo(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="gg2_names_", dir=WORK_DIR) as temp:
        temp_dir = Path(temp)
        raw = temp_dir / "block.raw"
        compressed = temp_dir / "block.lzo"
        raw.write_bytes(data)
        import subprocess

        subprocess.run([str(COMPRESSOR), str(raw), str(compressed)], check=True)
        return compressed.read_bytes()


def main() -> None:
    original = BASE_PACKAGE.read_bytes()
    expanded = BASE_EXPANDED.read_bytes()
    patched, delta, counts, changed_positions = patch_expanded(expanded)

    base.lzo1x_literal_block = compress_lzo
    # The serial size lives in chunk 0, while the personality labels and the
    # store welcome message are in two different sub-blocks of chunk 8. All
    # three affected sub-blocks must be rebuilt.
    rebuilt = original
    affected: set[tuple[int, int]] = set()
    original_infos = [base.chunk_info(original, i) for i in range(base.u32(original, base.CHUNK_COUNT_OFFSET))]
    for position in changed_positions:
        for chunk_index, info in enumerate(original_infos):
            uncompressed_offset, _, _, _, block_size, _, _ = info
            if uncompressed_offset <= position < uncompressed_offset + info[1]:
                affected.add((chunk_index, (position - uncompressed_offset) // block_size))
                break
        else:
            raise RuntimeError(f"GFX position outside compression chunks: {position:#x}")

    for chunk_index, block_index in sorted(affected):
        base.CHUNK_INDEX = chunk_index
        base.BLOCK_INDEX = block_index
        rebuilt = base.rebuild_package(rebuilt, patched)

    OUT_EXPANDED.write_bytes(patched)
    OUT_PACKAGE.write_bytes(rebuilt)
    print(f"text_delta={delta}")
    for source, count in counts:
        print(f"{source}: {count}")
    print(f"package_size={len(rebuilt)}")
    print(f"output={OUT_PACKAGE}")


if __name__ == "__main__":
    main()
