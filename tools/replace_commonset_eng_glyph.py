from pathlib import Path


GAME_PATH = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\Localization\INT\CommonSet_Eng.INT")
PATCH_PATH = Path(r"D:\GALGUNVV\GG2CNPatch_Distribution_Final_20260809\GG2Game\Localization\INT\CommonSet_Eng.INT")


def replace(path: Path) -> None:
    text = path.read_bytes().decode("utf-16")
    old = "Senpai直接上蜂巢了！"
    new = "Senpai直接上蜂窩了！"
    if text.count(old) != 1:
        raise RuntimeError(f"unexpected occurrence count in {path}: {text.count(old)}")
    path.write_text(text.replace(old, new), encoding="utf-16")


replace(GAME_PATH)
PATCH_PATH.write_bytes(GAME_PATH.read_bytes())
print("replaced CommonSet_Eng glyph")
