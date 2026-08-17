from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from translate_title_buttons import compress_dxt5


ROOT = Path(r"D:\GALGUNVV")
WORK = ROOT / "work"
FONT_PATH = r"C:\Windows\Fonts\msjhbd.ttc"

TITLE_RAW = WORK / "title_current_decompressed" / "LoadSwfMovieTitle_Eng.umap"
TITLE_OUT_RAW = WORK / "title_static_texts_cht" / "LoadSwfMovieTitle_Eng.umap"
TITLE_EXPORT = WORK / "title_ui_dds_export" / "LoadSwfMovieTitle_Eng" / "Texture2D"
TITLE_PNG_EXPORT = WORK / "title_all_export_eng" / "LoadSwfMovieTitle_Eng" / "Texture2D"
TITLE_CHINESE_EXPORT = WORK / "title_all_export_cht" / "LoadSwfMovieTitle" / "Texture2D"
TITLE_IMAGES = WORK / "title_static_texts_cht" / "title_textures"

BASE_RAW = WORK / "base_decompressed" / "LoadSwfMovieBase_Eng.umap"
BASE_OUT_RAW = WORK / "base_static_texts_cht" / "LoadSwfMovieBase_Eng.umap"
BASE_EXPORT = WORK / "base_dds_export" / "LoadSwfMovieBase_Eng" / "Texture2D"
BASE_IMAGES = WORK / "base_static_texts_cht" / "base_textures"


TITLE_TEXTURES = {
    "UICharaMake_Eng_I31": (0xEA3D44, 512, 64, "書呆子"),
    "UICharaMake_Eng_I37": (0xECC196, 512, 64, "運動派"),
    "UICharaMake_Eng_I3A": (0xED43BF, 512, 64, "時尚達人"),
    "UICharaMake_Eng_I3D": (0xEDC5E8, 512, 64, "變態"),
    "UICharaMake_Eng_I40": (0xEE4811, 512, 64, "平平無奇"),
    "UICharaMake_Eng_I46": (0xEFCC63, 512, 64, "紳士"),
    "UICharaMake_Eng_I4A": (0xF04E8C, 512, 64, "色鬼"),
    "UICharaMake_Eng_I4E": (0xF0D0B5, 512, 64, "那個厲害傢伙"),
    "UICharaMake_Eng_I54": (0xF55506, 1024, 128, "你的個性是？"),
}

BASE_TEXTURES = {
    "ScreenBase_Eng_I42": (0x599D20, 512, 64, "下一章節"),
    "ScreenBase_Eng_I4D": (0x5B6398, 512, 64, "學院商店"),
    "ScreenBase_Eng_I58": (0x7C6C37, 512, 64, "選項"),
    "ScreenBase_Eng_I60": (0x7D3087, 512, 64, "保存"),
    "ScreenBase_Eng_I68": (0x7DF4D7, 512, 64, "讀取"),
    "ScreenBase_Eng_I70": (0x7EB927, 512, 64, "返回標題畫面"),
}

BASE_TEXT_CENTERS = {
    # Match the visual center of the corresponding Japanese label textures.
    # The six source labels do not share one common center in their 512px
    # canvases, so centering every translation at the canvas midpoint shifts
    # the shorter labels on screen.
    "ScreenBase_Eng_I42": (260.0, 30.5),
    "ScreenBase_Eng_I4D": (257.0, 31.0),
    "ScreenBase_Eng_I58": (257.5, 30.5),
    "ScreenBase_Eng_I60": (260.0, 30.0),
    "ScreenBase_Eng_I68": (258.5, 30.5),
    "ScreenBase_Eng_I70": (258.5, 27.5),
}


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size, layout_engine=ImageFont.Layout.RAQM)


def fitted_font(text: str, max_width: int, max_height: int, start: int) -> ImageFont.FreeTypeFont:
    for size in range(start, 10, -1):
        candidate = font(size)
        left, top, right, bottom = candidate.getbbox(text, stroke_width=3)
        if right - left <= max_width and bottom - top <= max_height:
            return candidate
    return font(10)


def transparent_label(
    text: str,
    width: int,
    height: int,
    role: str,
    anchor: tuple[float, float] | None = None,
) -> Image.Image:
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    max_width = width - 24
    max_height = height - 8
    start = 48 if width == 512 else 52
    label_font = fitted_font(text, max_width, max_height, start)
    if role == "character":
        fill = (255, 255, 255, 255)
        outline = (0, 0, 0, 255)
    else:
        fill = (255, 255, 255, 255)
        outline = (49, 91, 205, 255)
    anchor_x, anchor_y = anchor or (width // 2, height // 2 + 1)
    draw.text(
        (anchor_x, anchor_y),
        text,
        font=label_font,
        anchor="mm",
        fill=fill,
        stroke_width=3,
        stroke_fill=outline,
    )
    return image


def question_banner(text: str) -> Image.Image:
    english = Image.open(TITLE_PNG_EXPORT / "UICharaMake_Eng_I54.png").convert("RGBA")
    japanese = Image.open(TITLE_CHINESE_EXPORT / "UICharaMake_I54.png").convert("RGBA")

    # Use both language variants to identify the old glyphs. The English and
    # Japanese labels share the same ribbon, while their glyph shapes differ.
    background = np.asarray(japanese.convert("RGB"), dtype=np.uint8).copy()
    english_rgb = np.asarray(english.convert("RGB"), dtype=np.uint8)
    japanese_rgb = background.copy()
    mask = np.zeros(background.shape[:2], dtype=np.uint8)
    region = np.zeros(mask.shape, dtype=bool)
    region[20:108, 0:1024] = True

    def glyph_pixels(rgb: np.ndarray) -> np.ndarray:
        brightness = rgb.mean(axis=2)
        spread = rgb.max(axis=2) - rgb.min(axis=2)
        white = (rgb.min(axis=2) > 105) & (spread < 145)
        black_outline = (brightness < 105) & (spread < 45)
        return (white | black_outline) & region

    mask[glyph_pixels(english_rgb) | glyph_pixels(japanese_rgb)] = 255
    mask = cv2.dilate(mask, np.ones((3, 3), dtype=np.uint8), iterations=1)
    restored = cv2.inpaint(cv2.cvtColor(background, cv2.COLOR_RGB2BGR), mask, 7, cv2.INPAINT_NS)
    image = Image.fromarray(cv2.cvtColor(restored, cv2.COLOR_BGR2RGB), "RGB").convert("RGBA")
    image.putalpha(english.getchannel("A"))

    draw = ImageDraw.Draw(image)
    label_font = fitted_font(text, 860, 78, 52)
    draw.text(
        (width := image.width // 2, image.height // 2),
        text,
        font=label_font,
        anchor="mm",
        fill=(255, 255, 255, 255),
        stroke_width=3,
        stroke_fill=(0, 0, 0, 255),
    )
    return image


def write_texture(image: Image.Image, directory: Path, name: str) -> bytes:
    directory.mkdir(parents=True, exist_ok=True)
    image.save(directory / f"{name}.png")
    payload = compress_dxt5(image)
    expected = image.width * image.height
    if len(payload) != expected:
        raise RuntimeError(f"{name}: DXT5 size {len(payload)} != {expected}")
    return payload


def patch_map(source_path: Path, output_path: Path, textures: dict, output_dir: Path, title: bool) -> None:
    source = source_path.read_bytes()
    output = bytearray(source)
    changes: list[tuple[int, int, int]] = []
    for name, (offset, width, height, text) in textures.items():
        if title and name.endswith("I54"):
            image = question_banner(text)
        elif title and name.endswith("I23"):
            image = Image.open(TITLE_CHINESE_EXPORT / "UICharaMake_I23.png").convert("RGBA")
        else:
            anchor = None if title else BASE_TEXT_CENTERS[name]
            image = transparent_label(text, width, height, "character" if title else "base", anchor)
        payload = write_texture(image, output_dir, name)
        old = source[offset:offset + len(payload)]
        if len(old) != len(payload):
            raise RuntimeError(f"{name}: raw map range is too short")
        output[offset:offset + len(payload)] = payload
        changes.append((offset, len(payload), int(old != payload)))
        print(f"{name}: {text} raw=0x{offset:X} bytes={len(payload)} changed={bool(old != payload)}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(output)
    print(f"wrote {output_path} ({len(output)} bytes)")
    print(f"payloads_changed={sum(item[2] for item in changes)}")


def main() -> None:
    if not TITLE_RAW.is_file() or not BASE_RAW.is_file():
        raise FileNotFoundError("decompressed map baseline is missing")

    # Keep the existing translated title buttons and add the remaining labels.
    title_textures = dict(TITLE_TEXTURES)
    title_textures["UICharaMake_Eng_I23"] = (0xD1B6C9, 512, 64, "2-E 久時 峰大")
    patch_map(TITLE_RAW, TITLE_OUT_RAW, title_textures, TITLE_IMAGES, title=True)
    patch_map(BASE_RAW, BASE_OUT_RAW, BASE_TEXTURES, BASE_IMAGES, title=False)


if __name__ == "__main__":
    main()
