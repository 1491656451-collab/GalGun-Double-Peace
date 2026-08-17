from pathlib import Path
import numpy as np
from PIL import Image

from translate_title_buttons import OFFSETS, EXPORT


def rgb565(v):
    return np.array([((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31], dtype=np.uint8)


def decode_dxt5(data, width, height):
    out = np.zeros((height, width, 4), dtype=np.uint8)
    pos = 0
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            a0, a1 = data[pos], data[pos + 1]
            bits = int.from_bytes(data[pos + 2:pos + 8], "little")
            ap = [a0, a1]
            if a0 > a1:
                ap += [(6 * a0 + a1) // 7, (5 * a0 + 2 * a1) // 7, (4 * a0 + 3 * a1) // 7,
                       (3 * a0 + 4 * a1) // 7, (2 * a0 + 5 * a1) // 7, (a0 + 6 * a1) // 7]
            else:
                ap += [(4 * a0 + a1) // 5, (3 * a0 + 2 * a1) // 5, (2 * a0 + 3 * a1) // 5,
                       (a0 + 4 * a1) // 5, 0, 255]
            c0 = int.from_bytes(data[pos + 8:pos + 10], "little")
            c1 = int.from_bytes(data[pos + 10:pos + 12], "little")
            cp = [rgb565(c0), rgb565(c1), (2 * rgb565(c0) + rgb565(c1)) // 3,
                  (rgb565(c0) + 2 * rgb565(c1)) // 3]
            cbits = int.from_bytes(data[pos + 12:pos + 16], "little")
            for j in range(4):
                for i in range(4):
                    yy, xx = y + j, x + i
                    if yy < height and xx < width:
                        out[yy, xx, :3] = cp[(cbits >> (2 * (j * 4 + i))) & 3]
                        out[yy, xx, 3] = ap[(bits >> (3 * (j * 4 + i))) & 7]
            pos += 16
    return out


tfc = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\CookedPC\Textures.tfc").read_bytes()
for name, offset in OFFSETS.items():
    width = 512 if name in {"I10", "I1A", "I22", "I28", "I2F", "I37", "I3F", "I45", "I4C", "I53", "I5A", "I61"} else 1024
    size = width * 128
    decoded = decode_dxt5(tfc[offset:offset + size], width, 128)
    source = np.asarray(Image.open(EXPORT / f"ScreenTitle_Eng_{name}.png").convert("RGBA"), dtype=np.uint8)
    diff = np.abs(decoded.astype(np.int16) - source.astype(np.int16))
    print(name, "offset", hex(offset), "mean", round(float(diff.mean()), 2), "max", int(diff.max()))
