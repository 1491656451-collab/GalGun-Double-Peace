from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from translate_title_buttons import compress_dxt5


ROOT = Path(r"D:\GALGUNVV")
WORK = ROOT / "work"
FONT_PATH = r"C:\Windows\Fonts\msjhbd.ttc"

RAW = WORK / "tutorial_destiny_decompressed_eng" / "Tutorial_Destiny_map_SwEng.umap"
OUT_RAW = WORK / "tutorial_destiny_static_cht" / "Tutorial_Destiny_map_SwEng.umap"
EXPORT = ROOT / "$out" / "Tutorial_Destiny_map_SwEng" / "Texture2D"
OUTPUT = WORK / "tutorial_destiny_static_cht" / "textures"

# UModel's serial offset for Tutorial06_Eng_I20 is 0x5FB049. UE3's texture
# payload starts 0x3F4 bytes into this serial and is one DXT5 byte per pixel.
TEXTURE_OFFSET = 0x5FB049 + 0x3F4
WIDTH, HEIGHT = 2048, 1024

# Coordinates are in the exported 2048x1024 tutorial image. Each rectangle
# covers only the old label glyph, leaving the icon and ribbon edges intact.
LABELS = {
    "Intelligence": ((1348, 369, 1510, 397), "智力"),
    "Athleticism": ((1348, 427, 1510, 455), "體能"),
    "Style": ((1348, 485, 1470, 513), "風格"),
    "Lewdness": ((1348, 543, 1510, 571), "好色程度"),
}


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size, layout_engine=ImageFont.Layout.RAQM)


def glyph_mask(image: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x1, y1, x2, y2 = box
    crop = image[y1:y2, x1:x2, :3]
    brightness = crop.mean(axis=2)
    spread = crop.max(axis=2) - crop.min(axis=2)
    # English glyphs are white with a dark outline on colored ribbons.
    white = (crop.min(axis=2) > 120) & (spread < 145)
    dark = (brightness < 105) & (spread < 55)
    mask = (white | dark).astype(np.uint8) * 255
    mask = cv2.dilate(mask, np.ones((3, 3), dtype=np.uint8), iterations=1)
    result = np.zeros(image.shape[:2], dtype=np.uint8)
    result[y1:y2, x1:x2] = mask
    return result


def render() -> Image.Image:
    source = Image.open(EXPORT / "Tutorial06_Eng_I20.png").convert("RGBA")
    rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
    mask = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    for box, _ in LABELS.values():
        mask = np.maximum(mask, glyph_mask(rgb, box))
    clean = cv2.inpaint(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), mask, 7, cv2.INPAINT_NS)
    image = Image.fromarray(cv2.cvtColor(clean, cv2.COLOR_BGR2RGB), "RGB").convert("RGBA")
    image.putalpha(source.getchannel("A"))

    draw = ImageDraw.Draw(image)
    for box, text in LABELS.values():
        x1, y1, x2, y2 = box
        label_font = font(30 if text != "好色程度" else 25)
        draw.text(
            ((x1 + x2) // 2, (y1 + y2) // 2 - 1),
            text,
            font=label_font,
            anchor="mm",
            fill=(255, 255, 255, 255),
            stroke_width=3,
            stroke_fill=(0, 0, 0, 255),
        )
    return image


def main() -> None:
    if not RAW.is_file():
        raise FileNotFoundError(RAW)
    image = render()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT / "Tutorial06_Eng_I20.png")
    payload = compress_dxt5(image)
    if len(payload) != WIDTH * HEIGHT:
        raise RuntimeError(f"unexpected DXT5 size: {len(payload)}")
    raw = RAW.read_bytes()
    if raw[TEXTURE_OFFSET:TEXTURE_OFFSET + len(payload)] == payload:
        raise RuntimeError("texture was not changed")
    output = bytearray(raw)
    output[TEXTURE_OFFSET:TEXTURE_OFFSET + len(payload)] = payload
    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)
    OUT_RAW.write_bytes(output)
    print(f"wrote {OUT_RAW} ({len(output)} bytes)")
    print(f"payload_offset=0x{TEXTURE_OFFSET:X} payload_size={len(payload)}")


if __name__ == "__main__":
    main()
