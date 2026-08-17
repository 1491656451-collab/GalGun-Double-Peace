from __future__ import annotations

import re
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from translate_title_buttons import compress_dxt5


ROOT = Path(r"D:\GALGUNVV")
WORK = ROOT / "work"
RAW_MAP = WORK / "collection_map_raw_20260808" / "GG2Collection_SwEng.umap"
OUT_MAP = WORK / "collection_map_raw_20260808" / "GG2Collection_SwEng_cht.umap"
TEXTURE_SOURCE = WORK / "collection_texture_export_eng" / "GG2Collection_SwEng" / "Texture2D"
TEXTURE_OUTPUT = WORK / "collection_texture_translated"
FONT_PATH = r"C:\Windows\Fonts\msjhbd.ttc"

TEXTURES = {
    "CllectTop_Eng_I11": (0x4029F15 + 0x1F3, "學生名冊", 42),
    "CllectTop_Eng_I17": (0x403E363 + 0x1F3, "我的資料", 42),
    "CllectTop_Eng_I1D": (0x40527B1 + 0x1F3, "畫廊", 52),
}

INT_SOURCE = Path(
    r"D:\虚幻解包\GALGUN汉化源文件\GG2CNPatch\out\INT\GG2GirlDatas.int"
)
INT_TARGETS = [
    Path(r"D:\GALGUNVV\work\collection_int_candidate\GG2GirlDatas.int"),
    Path(r"D:\GALGUNVV\work\collection_int_candidate\GG2GirlDatas_Eng.int"),
]
INT_CURRENT_ROOT = Path(
    r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\Localization\INT"
)


def localized_names(path: Path) -> dict[str, tuple[str, str]]:
    text = path.read_bytes().decode("utf-16")
    result: dict[str, tuple[str, str]] = {}
    pattern = re.compile(
        r"\[localizedData\.([^ ]+)\b.*?"
        r"^firstName=\"([^\"]*)\"\s*$.*?"
        r"^lastName=\"([^\"]*)\"\s*$",
        re.MULTILINE | re.DOTALL,
    )
    for match in pattern.finditer(text):
        result[match.group(1)] = (match.group(2), match.group(3))
    result.update(
        {
            "76_YUREINO_YUKO": ("未知", "未知"),
            "77_SHIAWASE_HUMAN": ("幸福", "人"),
            "78_FUSHIAWASE_HUMAN": ("不幸福", "人"),
        }
    )
    if len(result) != 79:
        raise RuntimeError(f"expected 79 girl names, found {len(result)} in {path}")
    return result


def patch_int_file(source: Path, destination: Path, names: dict[str, tuple[str, str]]) -> None:
    text = source.read_bytes().decode("utf-16")
    for key, (first, last) in names.items():
        block_pattern = re.compile(
            rf"(?P<prefix>\[localizedData\.{re.escape(key)}\b.*?)(?P<end>\r?\n\r?\n\[localizedData\.|\Z)",
            re.MULTILINE | re.DOTALL,
        )
        match = block_pattern.search(text)
        if not match:
            raise RuntimeError(f"missing localizedData block: {key}")
        block = match.group("prefix")
        block, first_count = re.subn(
            r"(?m)^firstName=\"[^\"]*\"\r*$",
            f'firstName="{first}"',
            block,
            count=1,
        )
        block, last_count = re.subn(
            r"(?m)^lastName=\"[^\"]*\"\r*$",
            f'lastName="{last}"',
            block,
            count=1,
        )
        if first_count != 1 or last_count != 1:
            raise RuntimeError(f"missing name field in {key}")
        text = text[: match.start("prefix")] + block + text[match.end("prefix") :]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(b"\xff\xfe" + text.encode("utf-16-le"))


def render_label(text: str, size: int) -> Image.Image:
    source = Image.open(TEXTURE_SOURCE / "CllectTop_Eng_I11.png").convert("RGBA")
    image = Image.new("RGBA", source.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_PATH, size, layout_engine=ImageFont.Layout.RAQM)
    draw.text(
        (image.width // 2, image.height // 2),
        text,
        font=font,
        anchor="mm",
        fill=(255, 255, 255, 255),
    )
    return image


def patch_map() -> None:
    source = RAW_MAP.read_bytes()
    output = bytearray(source)
    for name, (offset, text, size) in TEXTURES.items():
        image = render_label(text, size)
        payload = compress_dxt5(image)
        if len(payload) != 256 * 64:
            raise RuntimeError(f"unexpected DXT5 size for {name}: {len(payload)}")
        old = source[offset : offset + len(payload)]
        if len(old) != len(payload):
            raise RuntimeError(f"texture range exceeds raw map: {name}")
        output[offset : offset + len(payload)] = payload
        TEXTURE_OUTPUT.mkdir(parents=True, exist_ok=True)
        image.save(TEXTURE_OUTPUT / f"{name}.png")
        print(f"{name}: {text}, raw=0x{offset:X}, changed={old != payload}")
    OUT_MAP.write_bytes(output)
    print(f"wrote {OUT_MAP} ({len(output)} bytes)")


def main() -> None:
    names = localized_names(INT_SOURCE)
    for target in INT_TARGETS:
        current = INT_CURRENT_ROOT / target.name
        patch_int_file(current, target, names)
        print(f"wrote {target}")
    patch_map()


if __name__ == "__main__":
    main()
