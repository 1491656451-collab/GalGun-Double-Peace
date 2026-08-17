from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from translate_title_buttons import compress_dxt5


ROOT = Path(r"D:\GALGUNVV")
FONT = Path(r"C:\Windows\Fonts\msjhbd.ttc")
SHOOTING_RAW = ROOT / "work" / "shooting_decompressed" / "LoadSwfMovieShooting_Eng.umap"
TEXTURE_OUT = ROOT / "work" / "pause_textures_cht"


def fitted_font(text: str, max_width: int, size: int) -> ImageFont.FreeTypeFont:
    for candidate_size in range(size, 12, -1):
        candidate = ImageFont.truetype(str(FONT), candidate_size)
        box = candidate.getbbox(text, stroke_width=3)
        if box[2] - box[0] <= max_width:
            return candidate
    return ImageFont.truetype(str(FONT), 12)


def label(title: str, subtitle: str) -> Image.Image:
    image = Image.new("RGBA", (512, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    title_font = fitted_font(title, 460, 54)
    subtitle_font = fitted_font(subtitle, 460, 31)
    outline = (0, 20, 145, 255)
    draw.text((256, 39), title, font=title_font, anchor="mm", fill="white", stroke_width=3, stroke_fill=outline)
    draw.text((256, 94), subtitle, font=subtitle_font, anchor="mm", fill="white", stroke_width=3, stroke_fill=outline)
    return image


def write_texture(name: str, image: Image.Image, offset: int) -> None:
    payload = compress_dxt5(image)
    if len(payload) != 512 * 128:
        raise RuntimeError(f"{name}: unexpected DXT5 size {len(payload)}")
    TEXTURE_OUT.mkdir(parents=True, exist_ok=True)
    image.save(TEXTURE_OUT / f"{name}.png")
    data = bytearray(SHOOTING_RAW.read_bytes()) if not hasattr(write_texture, "data") else write_texture.data
    old = bytes(data[offset : offset + len(payload)])
    if len(old) != len(payload):
        raise RuntimeError(f"{name}: texture range is truncated")
    data[offset : offset + len(payload)] = payload
    write_texture.data = data
    print(f"{name}: offset=0x{offset:X} bytes={len(payload)} changed={old != payload}")


def main() -> None:
    if not SHOOTING_RAW.is_file():
        raise FileNotFoundError(SHOOTING_RAW)
    write_texture.data = bytearray(SHOOTING_RAW.read_bytes())
    write_texture("ScreenContinue_Eng_I18", label("放棄……", "（返回主選單）"), 0x6A025)
    write_texture("ScreenContinue_Eng_IB", label("繼續！", "（使用MP復活）"), 0xB73AF)
    SHOOTING_RAW.write_bytes(write_texture.data)
    print(f"wrote {SHOOTING_RAW} ({SHOOTING_RAW.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
