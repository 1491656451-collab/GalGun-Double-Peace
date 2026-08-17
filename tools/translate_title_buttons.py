from pathlib import Path
import struct

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\GALGUNVV")
EXPORT = ROOT / "work" / "title_texture_export" / "LoadSwfMovieTitle_Eng" / "Texture2D"
JPN_EXPORT = ROOT / "work" / "title_texture_export_jpn" / "LoadSwfMovieTitle" / "Texture2D"
OUT_IMAGES = ROOT / "work" / "title_texture_translated"
SOURCE_MAP = ROOT / "work" / "title_decompressed_explicit" / "LoadSwfMovieTitle_Eng.umap"
OUT_MAP = ROOT / "work" / "LoadSwfMovieTitle_Eng_cht.umap"
FONT = r"C:\Windows\Fonts\msjhbd.ttc"


BUTTONS = {
    "I10": "專家", "I13": "專家",
    "I1A": "初學者", "I1D": "初學者",
    "I22": "下載", "I24": "下載",
    "I28": "上傳", "I2A": "上傳",
    "I2F": "繼續", "I32": "繼續",
    "I37": "開始遊戲", "I3A": "開始遊戲",
    "I3F": "離開", "I41": "離開",
    "I45": "選項", "I48": "選項",
    "I4C": "更衣室", "I4F": "更衣室",
    "I53": "收藏", "I56": "收藏",
    "I5A": "分數挑戰", "I5D": "分數挑戰",
    "I61": "故事", "I64": "故事",
}

# Width of the original label area in the 512px variant. The 1024px
# variants use the same label scale, but are centered in a wider texture.
LABEL_MASK_WIDTHS = {
    "I10": 210, "I13": 210,
    "I1A": 265, "I1D": 265,
    "I22": 270, "I24": 270,
    "I28": 220, "I2A": 220,
    "I2F": 265, "I32": 265,
    "I37": 310, "I3A": 310,
    "I3F": 165, "I41": 165,
    "I45": 250, "I48": 250,
    "I4C": 380, "I4F": 380,
    "I53": 290, "I56": 290,
    "I5A": 330, "I5D": 330,
    "I61": 180, "I64": 180,
}


OFFSETS = {
    "I10": 0x21E3E8, "I13": 0x22E611,
    "I1A": 0x24FA63, "I1D": 0x25FC8C,
    "I22": 0x27FEB5, "I24": 0x2900DE,
    "I28": 0x2B0307, "I2A": 0x2C0530,
    "I2F": 0x2E0759, "I32": 0x2F0982,
    "I37": 0x310BAB, "I3A": 0x320DD4,
    "I3F": 0x340FFD, "I41": 0x351226,
    "I45": 0x37144F, "I48": 0x381678,
    "I4C": 0x3A18A1, "I4F": 0x3B1ACA,
    "I53": 0x3D1CF3, "I56": 0x3E1F1C,
    "I5A": 0x402145, "I5D": 0x41236E,
    "I61": 0x6327BF, "I64": 0x6429E8,
}


def rgb565_to_rgb(value):
    r = ((value >> 11) & 31) * 255 // 31
    g = ((value >> 5) & 63) * 255 // 63
    b = (value & 31) * 255 // 31
    return np.array([r, g, b], dtype=np.int32)


def rgb_to_565(rgb):
    r, g, b = [int(x) for x in rgb]
    return ((r * 31 // 255) << 11) | ((g * 63 // 255) << 5) | (b * 31 // 255)


def color_palette(c0, c1):
    a = rgb565_to_rgb(c0)
    b = rgb565_to_rgb(c1)
    return np.array([a, b, (2 * a + b) // 3, (a + 2 * b) // 3], dtype=np.int32)


def compress_alpha(block):
    values = block.reshape(-1).astype(np.int32)
    a0 = int(values.max())
    a1 = int(values.min())
    if a0 == a1:
        return bytes((a0, a1)) + b"\x00" * 6
    palette = [a0, a1]
    if a0 > a1:
        palette.extend((6 * a0 + a1) // 7 for _ in [0])
        palette.extend((5 * a0 + 2 * a1) // 7 for _ in [0])
        palette.extend((4 * a0 + 3 * a1) // 7 for _ in [0])
        palette.extend((3 * a0 + 4 * a1) // 7 for _ in [0])
        palette.extend((2 * a0 + 5 * a1) // 7 for _ in [0])
        palette.extend((a0 + 6 * a1) // 7 for _ in [0])
    else:
        palette.extend((4 * a0 + a1) // 5 for _ in [0])
        palette.extend((3 * a0 + 2 * a1) // 5 for _ in [0])
        palette.extend((2 * a0 + 3 * a1) // 5 for _ in [0])
        palette.extend((a0 + 4 * a1) // 5 for _ in [0])
        palette.extend((0, 255))
    indices = [min(range(8), key=lambda i: abs(values[p] - palette[i])) for p in range(16)]
    packed = sum((index & 7) << (3 * p) for p, index in enumerate(indices))
    return bytes((a0, a1)) + packed.to_bytes(6, "little")


def compress_color(block):
    pixels = block.reshape(-1, 3).astype(np.int32)
    candidates = {rgb_to_565(pixel) for pixel in pixels}
    mins = pixels.min(axis=0)
    maxs = pixels.max(axis=0)
    for r in (mins[0], maxs[0]):
        for g in (mins[1], maxs[1]):
            for b in (mins[2], maxs[2]):
                candidates.add(rgb_to_565((r, g, b)))
    candidates = list(candidates)
    best = None
    for c0 in candidates:
        for c1 in candidates:
            if c0 <= c1:
                continue
            palette = color_palette(c0, c1)
            distances = ((pixels[:, None, :] - palette[None, :, :]) ** 2).sum(axis=2)
            indices = distances.argmin(axis=1)
            error = int(distances[np.arange(16), indices].sum())
            if best is None or error < best[0]:
                best = (error, c0, c1, indices)
    if best is None:
        c = candidates[0] if candidates else 0
        best = (0, max(c, 1), 0, np.zeros(16, dtype=np.int32))
    _, c0, c1, indices = best
    packed = sum((int(index) & 3) << (2 * p) for p, index in enumerate(indices))
    return struct.pack("<HHI", c0, c1, packed)


def compress_dxt5(image):
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    height, width, _ = rgba.shape
    output = bytearray()
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            block = rgba[y:y + 4, x:x + 4]
            alpha = np.zeros((4, 4), dtype=np.uint8)
            rgb = np.zeros((4, 4, 3), dtype=np.uint8)
            alpha[:block.shape[0], :block.shape[1]] = block[:, :, 3]
            rgb[:block.shape[0], :block.shape[1]] = block[:, :, :3]
            output.extend(compress_alpha(alpha))
            output.extend(compress_color(rgb))
    return bytes(output)


STATE_GROUPS = {
    512: ["I10", "I1A", "I22", "I28", "I2F", "I37", "I3F", "I45", "I4C", "I53", "I5A", "I61"],
    1024: ["I13", "I1D", "I24", "I2A", "I32", "I3A", "I41", "I48", "I4F", "I56", "I5D", "I64"],
}
PINK_BUTTONS = {
    "I13", "I1D", "I24", "I2A", "I32", "I3A",
    "I41", "I48", "I4F", "I56", "I5D", "I64",
}
BACKGROUND_CACHE = {}


def label_mask(name, source, dilation=7):
    """Return a mask for the old English glyph and its colored outline."""
    rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
    height, width = rgb.shape[:2]
    center = width // 2
    mask_width = LABEL_MASK_WIDTHS[name]
    left = max(0, center - mask_width // 2 - 10)
    right = min(width, center + (mask_width + 1) // 2 + 10)
    values = rgb.astype(np.int16)
    neutral_white = (
        (values.min(axis=2) > 100)
        & ((values.max(axis=2) - values.min(axis=2)) < 100)
    )
    candidates = np.zeros((height, width), dtype=np.uint8)
    candidates[34:94, left:right] = neutral_white[34:94, left:right]
    count, labels, stats, _ = cv2.connectedComponentsWithStats(candidates, 8)
    mask = np.zeros((height, width), dtype=np.uint8)
    for component in range(1, count):
        x, y, component_width, component_height, area = stats[component]
        if area >= 3 and component_height >= 2:
            mask[labels == component] = 255
    if dilation:
        kernel_size = dilation * 2 + 1
        mask = cv2.dilate(mask, np.ones((kernel_size, kernel_size), dtype=np.uint8), 1)
    return mask


def background_model(width):
    group = STATE_GROUPS[width]
    paths = [EXPORT / f"ScreenTitle_Eng_{item}.png" for item in group]
    paths.extend(JPN_EXPORT / f"screentitle_{item}.png" for item in group)
    images = np.stack([
        np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)
        for path in paths
    ], axis=0)
    masked = images.astype(np.float32)
    for index, name in enumerate(group * 2):
        masked[index][label_mask(name, Image.fromarray(images[index]), dilation=0) > 0] = np.nan
    model = np.nanmedian(masked, axis=0)
    fallback = np.median(images.astype(np.float32), axis=0)
    model = np.where(np.isfinite(model), model, fallback)
    return np.rint(model).astype(np.uint8)


def text_bounds(name, source):
    """Find a tight box around the original English label."""
    rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
    height, width = rgb.shape[:2]
    center = width // 2
    mask_width = LABEL_MASK_WIDTHS[name]
    left = max(0, center - mask_width // 2 - 10)
    right = min(width, center + (mask_width + 1) // 2 + 10)
    values = rgb.astype(np.int16)
    candidate = (
        (values.min(axis=2) > 100)
        & ((values.max(axis=2) - values.min(axis=2)) < 100)
    )
    candidate[:36] = False
    candidate[94:] = False
    candidate[:, :left] = False
    candidate[:, right:] = False
    count, labels, stats, _ = cv2.connectedComponentsWithStats(candidate.astype(np.uint8), 8)
    components = [
        stats[index]
        for index in range(1, count)
        if stats[index, 4] >= 20 and stats[index, 3] >= 7
    ]
    if not components:
        return left, 36, right, 94
    x1 = max(left, min(int(component[0]) for component in components) - 18)
    y1 = max(28, min(int(component[1]) for component in components) - 14)
    x2 = min(right, max(int(component[0] + component[2]) for component in components) + 18)
    y2 = min(102, max(int(component[1] + component[3]) for component in components) + 14)
    return x1, y1, x2, y2


def pink_background():
    """Rebuild the pink button center from its text-free 16px background tile."""
    reference = np.asarray(
        Image.open(JPN_EXPORT / "screentitle_I56.png").convert("RGB"),
        dtype=np.uint8,
    )
    background = reference.copy()
    # x=260 is a transition column; x=268 begins a seamless 16px period.
    tile_start = 268
    tile_width = 16
    for x in range(tile_start, reference.shape[1] - tile_start):
        source_x = tile_start + ((x - tile_start) % tile_width)
        background[28:103, x] = reference[28:103, source_x]
    return background


def clean_background(name, source):
    width, height = source.size
    cache_key = (width, "pink" if name in PINK_BUTTONS else "blue")
    if cache_key not in BACKGROUND_CACHE:
        BACKGROUND_CACHE[cache_key] = (
            pink_background() if name in PINK_BUTTONS else background_model(width)
        )
    background = BACKGROUND_CACHE[cache_key]
    if name in PINK_BUTTONS:
        # The reference has the same selected-state button geometry and alpha;
        # using its rebuilt center removes every pixel of the old label.
        source_rgb = background.copy()
    else:
        source_rgb = np.asarray(source.convert("RGB"), dtype=np.uint8).copy()
        x1, y1, x2, y2 = text_bounds(name, source)
        source_rgb[y1:y2, x1:x2] = background[y1:y2, x1:x2]
    result = Image.fromarray(source_rgb, "RGB").convert("RGBA")
    result.putalpha(source.getchannel("A"))
    return result


def render_button(name, text):
    source = Image.open(EXPORT / f"ScreenTitle_Eng_{name}.png").convert("RGBA")
    width, height = source.size
    result = clean_background(name, source)
    draw = ImageDraw.Draw(result)
    size = 54 if width == 512 else 54
    font = ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)
    pink = name in {"I13", "I1D", "I24", "I2A", "I32", "I3A", "I41", "I48", "I4F", "I56", "I5D", "I64"}
    fill = (255, 38, 103, 255) if pink else (255, 255, 255, 255)
    stroke = (255, 255, 255, 255) if pink else (0, 74, 167, 255)
    if pink:
        stroke_width = 3
    else:
        stroke_width = 3
    draw.text((width // 2, height // 2 + 1), text, font=font, anchor="mm", fill=fill,
              stroke_width=stroke_width, stroke_fill=stroke)
    OUT_IMAGES.mkdir(parents=True, exist_ok=True)
    result.save(OUT_IMAGES / f"ScreenTitle_Eng_{name}.png")
    return compress_dxt5(result)


def main():
    source = SOURCE_MAP.read_bytes()
    output = bytearray(source)
    for name, text in BUTTONS.items():
        data = render_button(name, text)
        path = OUT_IMAGES / f"ScreenTitle_Eng_{name}.png"
        width = 512 if name in {"I10", "I1A", "I22", "I28", "I2F", "I37", "I3F", "I45", "I4C", "I53", "I5A", "I61"} else 1024
        expected = width * 128
        if len(data) != expected:
            raise RuntimeError(f"{name}: DXT5 size {len(data)} != {expected}")
        offset = OFFSETS[name]
        old = source[offset:offset + expected]
        if len(old) != expected:
            raise RuntimeError(f"{name}: source range is too short")
        output[offset:offset + expected] = data
        print(f"{name}: {text} {width}x128 raw={len(data)} changed={old != data}")
    OUT_MAP.write_bytes(output)
    print(f"wrote {OUT_MAP} ({len(output)} bytes)")


if __name__ == "__main__":
    main()
