from __future__ import annotations

import re
import struct
from pathlib import Path


GAME_PACKAGE = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\CookedPC\GG2Game.u")
EXPANDED_PACKAGE = Path(r"D:\GALGUNVV\$out\GG2Game.u")
SHOP_CONFIG = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\Config\GG2GG2HudUIShopActor.ini")
WORK_DIR = Path(r"D:\GALGUNVV\work\shop_package_rebuild")
OUT_PACKAGE = WORK_DIR / "GG2Game.u.shopnames.modified"
OUT_EXPANDED = WORK_DIR / "GG2Game.u.shopnames.expanded"

ENGLISH_NAMES = [
    "Red Energy Drink LV1", "Red Energy Drink LV2", "Red Energy Drink LV3",
    "Red Energy Drink LV4", "Red Energy Drink LV5", "Blue Energy Drink LV1",
    "Blue Energy Drink LV2", "Blue Energy Drink LV3", "Blue Energy Drink LV4",
    "Blue Energy Drink LV5", "Green Energy Drink LV1", "Green Energy Drink LV2",
    "Green Energy Drink LV3", "Doki-Doki Camera 2", "Doki-Doki Camera 3",
    "Angel Groin Protector", "Angel Oil", "Angel Ear Plugs", "Angel Eye Drops",
    "Measuring Tape", "Destiny Arrow Charm", "Swirly Glasses", "Iron Dumbbell",
    "Fashion Magazine", "Oh My, Senpai", "Cursed Glasses", "Cursed Dumbbell",
    "Lame Fashion Mag", "Chastity 4 Dummies", "Donate to LOVEHEARTS",
    "Donate to LOVEHEARTS", "Donate to LOVEHEARTS", "Donate to LOVEHEARTS",
    "Donate to LOVEHEARTS", "Unused Item Frame", "Pheromone Z",
    "Angel Cutting Board", "Demon Pork Buns",
]

PACKAGE_TAG = 0x9E2A83C1
TABLE_OFFSET = 0x75
CHUNK_COUNT_OFFSET = 0x71
CHUNK_ENTRY_SIZE = 16
CHUNK_INDEX = 8
BLOCK_INDEX = 2
SHOP_OBJECT_END = 0xC8AA5D


def u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def put_u32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value)


def chunk_info(data: bytes, index: int) -> tuple[int, int, int, int, int, int, int]:
    base = TABLE_OFFSET + index * CHUNK_ENTRY_SIZE
    uncompressed_offset, uncompressed_size, compressed_offset, compressed_size = struct.unpack_from(
        "<4I", data, base
    )
    tag, block_size, compressed_total, uncompressed_total = struct.unpack_from(
        "<4I", data, compressed_offset
    )
    if tag != PACKAGE_TAG or uncompressed_size != uncompressed_total:
        raise RuntimeError(f"invalid chunk {index}: {hex(compressed_offset)}")
    block_count = (uncompressed_total + block_size - 1) // block_size
    header_size = 16 + block_count * 8
    if compressed_total + header_size != compressed_size:
        raise RuntimeError(f"chunk {index} size mismatch")
    return (
        uncompressed_offset,
        uncompressed_size,
        compressed_offset,
        compressed_size,
        block_size,
        block_count,
        header_size,
    )


def target_names() -> list[str]:
    raw = SHOP_CONFIG.read_bytes()
    text = raw.decode("utf-16-le") if raw.startswith(b"\xff\xfe") else raw.decode("utf-8")
    names = re.findall(r'goodsName\[0\]="([^"]*)"', text)
    if len(names) != len(ENGLISH_NAMES):
        raise RuntimeError(f"expected 38 target names, found {len(names)}")
    return names


def patch_expanded(expanded: bytes, names: list[str]) -> tuple[bytes, int]:
    buffer = bytearray(expanded)
    region_start = 0xC85000
    region_end = 0xC8A000
    replacements: list[tuple[int, int, bytes]] = []
    search_start = region_start
    for english, traditional in zip(ENGLISH_NAMES, names):
        needle = english.encode("ascii") + b"\0"
        pos = expanded.find(needle, search_start, region_end)
        if pos < 4:
            raise RuntimeError(f"missing serialized name: {english}")
        search_start = pos + len(needle)
        old_length = 4 + len(needle)
        encoded = traditional.encode("utf-16-le") + b"\0\0"
        replacement = struct.pack("<i", -(len(traditional) + 1)) + encoded
        replacements.append((pos - 4, old_length, replacement))

    delta = sum(len(new) - old_len for _, old_len, new in replacements)
    if SHOP_OBJECT_END <= replacements[-1][0]:
        raise RuntimeError("shop object boundary is before the last replacement")

    cursor = 0
    rebuilt = bytearray()
    for start, old_len, replacement in replacements:
        rebuilt.extend(expanded[cursor:start])
        rebuilt.extend(replacement)
        cursor = start + old_len
    rebuilt.extend(expanded[cursor:SHOP_OBJECT_END])
    rebuilt.extend(b"\0" * (-delta))
    rebuilt.extend(expanded[SHOP_OBJECT_END:])
    if len(rebuilt) != len(expanded):
        raise RuntimeError(f"expanded size changed: {len(rebuilt)} vs {len(expanded)}")

    for name in names:
        if name.encode("utf-16-le") not in rebuilt[region_start:region_end]:
            raise RuntimeError(f"patched name not found: {name}")
    return bytes(rebuilt), delta


def lzo1x_literal_block(data: bytes) -> bytes:
    """Encode a block as a valid LZO1X stream containing only literals."""
    if len(data) < 4:
        raise RuntimeError("LZO literal stream requires at least 4 bytes")

    encoded = bytearray()
    if len(data) <= 18:
        encoded.append(len(data) + 17)
    else:
        encoded.append(0)
        remaining = len(data) - 18
        while remaining > 255:
            encoded.append(0)
            remaining -= 255
        encoded.append(remaining)
    encoded.extend(data)
    encoded.extend((0x11, 0x00, 0x00))
    return bytes(encoded)


def rebuild_package(original: bytes, patched_expanded: bytes) -> bytes:
    count = u32(original, CHUNK_COUNT_OFFSET)
    if count != 0xAE:
        raise RuntimeError(f"unexpected chunk count: {count}")
    infos = [chunk_info(original, i) for i in range(count)]
    chunk = infos[CHUNK_INDEX]
    uncompressed_offset, uncompressed_size, compressed_offset, compressed_size, block_size, block_count, header_size = chunk
    block_data_offset = compressed_offset + header_size
    block_offsets: list[tuple[int, int, int]] = []
    cursor = block_data_offset
    for block_index in range(block_count):
        compressed_size_i, uncompressed_size_i = struct.unpack_from("<2I", original, compressed_offset + 16 + block_index * 8)
        block_offsets.append((cursor, compressed_size_i, uncompressed_size_i))
        cursor += compressed_size_i
    if cursor != compressed_offset + compressed_size:
        raise RuntimeError("compressed block layout mismatch")

    target_start = uncompressed_offset + BLOCK_INDEX * block_size
    target_end = target_start + block_offsets[BLOCK_INDEX][2]
    raw_block = patched_expanded[target_start:target_end]
    if len(raw_block) != block_offsets[BLOCK_INDEX][2]:
        raise RuntimeError("patched block size mismatch")
    new_block = lzo1x_literal_block(raw_block)

    old_block_size = block_offsets[BLOCK_INDEX][1]
    new_block_size = len(new_block)
    delta = new_block_size - old_block_size

    chunk_header = bytearray(original[compressed_offset:compressed_offset + header_size])
    put_u32(chunk_header, 8, u32(chunk_header, 8) + delta)
    put_u32(chunk_header, 16 + BLOCK_INDEX * 8, new_block_size)

    new_chunk = bytearray(chunk_header)
    for i, (block_offset, old_size, _) in enumerate(block_offsets):
        if i == BLOCK_INDEX:
            new_chunk.extend(new_block)
        else:
            new_chunk.extend(original[block_offset:block_offset + old_size])

    if len(new_chunk) != compressed_size + delta:
        raise RuntimeError("rebuilt chunk size mismatch")

    package = bytearray()
    package.extend(original[:compressed_offset])
    package.extend(new_chunk)
    package.extend(original[compressed_offset + compressed_size:])

    for i, (_, _, old_offset, old_size, _, _, _) in enumerate(infos):
        table_entry = TABLE_OFFSET + i * CHUNK_ENTRY_SIZE
        new_size = old_size
        new_offset = old_offset
        if i == CHUNK_INDEX:
            new_size += delta
        elif old_offset > compressed_offset:
            new_offset += delta
        put_u32(package, table_entry + 8, new_offset)
        put_u32(package, table_entry + 12, new_size)
    return bytes(package)


def main() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    original = GAME_PACKAGE.read_bytes()
    expanded = EXPANDED_PACKAGE.read_bytes()
    names = target_names()
    patched_expanded, text_delta = patch_expanded(expanded, names)
    rebuilt = rebuild_package(original, patched_expanded)
    OUT_EXPANDED.write_bytes(patched_expanded)
    OUT_PACKAGE.write_bytes(rebuilt)
    print(f"names={len(names)} text_delta={text_delta}")
    print(f"original={len(original)} rebuilt={len(rebuilt)}")
    print(f"out={OUT_PACKAGE}")


if __name__ == "__main__":
    main()
