from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from translate_title_buttons import compress_dxt5


ROOT = Path(r"D:\GALGUNVV")
WORK = ROOT / "work"
RAW_PACKAGE = WORK / "current_gg2game_verify" / "GG2Game.u"
OUT_PACKAGE = WORK / "windowstate_labels_cht_expanded" / "GG2Game.u"
SOURCE_PNG = WORK / "windowstate_texture_export" / "GG2Game" / "Texture2D" / "WindowState_I1.png"
JPN_PNG = ROOT / "$out" / "GG2Game" / "Texture2D" / "WindowState_I3.png"
OUT_PNG = WORK / "windowstate_labels_cht_expanded" / "WindowState_I1.png"
FONT_PATH = r"C:\Windows\Fonts\msjhbd.ttc"

# WindowState_I1 is a 1024x512 DXT5 texture. The serial begins at the
# exported object offset 0xA56C9E3 and its inline mip payload begins at +0x1F0.
TEXTURE_PAYLOAD_OFFSET = 0xA56CBD3
TEXTURE_WIDTH = 1024
TEXTURE_HEIGHT = 512

LABELS = [
    ((365, 102), "智力"),
    ((365, 196), "體能"),
    ((365, 294), "風格"),
    ((365, 388), "好色程度"),
]

# The Japanese texture has the same panel art and shorter labels. Rebuilding
# these small label bands from their clean left/right edges removes both the
# English and Japanese glyphs without touching the chevrons on the right.
BAND_REPAIRS = [
    ((350, 84, 450, 132), 450),
    ((350, 180, 450, 226), 450),
    ((325, 276, 495, 324), 495),
    ((340, 372, 475, 416), 475),
]


def make_background(source: np.ndarray, japanese: np.ndarray) -> np.ndarray:
    result = japanese.copy()
    for (x1, y1, x2, y2), right_x in BAND_REPAIRS:
        for y in range(y1, y2):
            left = result[y, x1 - 1, :3].astype(np.float32)
            right = result[y, right_x, :3].astype(np.float32)
            weights = np.linspace(0.0, 1.0, x2 - x1, dtype=np.float32)[:, None]
            row = np.rint(left[None, :] * (1.0 - weights) + right[None, :] * weights)
            result[y, x1:x2, :3] = row.astype(np.uint8)
    return result


def render() -> Image.Image:
    source = np.asarray(Image.open(SOURCE_PNG).convert("RGBA"), dtype=np.uint8)
    japanese = np.asarray(Image.open(JPN_PNG).convert("RGBA"), dtype=np.uint8)
    if source.shape != (TEXTURE_HEIGHT, TEXTURE_WIDTH, 4):
        raise RuntimeError(f"unexpected source dimensions: {source.shape}")
    if japanese.shape != source.shape:
        raise RuntimeError(f"English/Japanese texture dimensions differ: {japanese.shape}")

    rgba = make_background(source, japanese)
    image = Image.fromarray(rgba, "RGBA")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_PATH, 46, layout_engine=ImageFont.Layout.RAQM)
    for left, text in LABELS:
        draw.text(
            left,
            text,
            font=font,
            anchor="lm",
            fill=(255, 255, 255, 255),
            stroke_width=3,
            stroke_fill=(0, 0, 0, 255),
        )
    return image


def main() -> None:
    image = render()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT_PNG)
    payload = compress_dxt5(image)
    expected = TEXTURE_WIDTH * TEXTURE_HEIGHT
    if len(payload) != expected:
        raise RuntimeError(f"unexpected DXT5 size: {len(payload)} != {expected}")

    raw = bytearray(RAW_PACKAGE.read_bytes())
    old = bytes(raw[TEXTURE_PAYLOAD_OFFSET:TEXTURE_PAYLOAD_OFFSET + len(payload)])
    if len(old) != len(payload):
        raise RuntimeError("texture payload range is outside expanded package")
    if old == payload:
        raise RuntimeError("texture payload was not changed")
    raw[TEXTURE_PAYLOAD_OFFSET:TEXTURE_PAYLOAD_OFFSET + len(payload)] = payload
    OUT_PACKAGE.write_bytes(raw)
    print(f"wrote {OUT_PACKAGE} ({len(raw)} bytes)")
    print(f"wrote {OUT_PNG}")
    print(f"payload_offset=0x{TEXTURE_PAYLOAD_OFFSET:X} payload_size={len(payload)}")


if __name__ == "__main__":
    main()
