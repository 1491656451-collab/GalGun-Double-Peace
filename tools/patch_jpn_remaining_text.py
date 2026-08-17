from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil


GAME = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace")
JPN = GAME / "GG2Game" / "Localization" / "JPN"


REPLACEMENTS = {
    "GG2Game.jpn": {
        "Bookworm": "書呆子",
        "Jock": "運動派",
        "Fashionista": "時尚達人",
        "Pervert": "變態",
        "Nothing Special": "平平無奇",
        "Gentleman": "紳士",
        "Hentai Fiend": "色鬼",
        "TFG (That Friggin' Guy)": "那個厲害傢伙",
        "lewdness": "好色",
    },
    "Tutorial_Destiny_ENG.jpn": {
        "If your intelligence, athleticism, style /nand lewdness parameters match with their /nfavorite, your affection level will increase.":
            "如果你的智力、體能、風格和好色程度符合她們喜好的話，命運度就會提升。",
    },
    "Common_Prologue_ENG.jpn": {
        "My name is Houdai Kudoki.": "我的名字是峯大九，",
    },
}


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("cp932")


def patch_file(path: Path, replacements: dict[str, str], stamp: str) -> None:
    text = read_text(path)
    original = text
    for source, target in replacements.items():
        count = text.count(source)
        if not count:
            raise RuntimeError(f"{path.name}: missing {source!r}")
        text = text.replace(source, target)
        print(f"{path.name}: {source!r} -> {target!r} ({count})")

    backup = path.with_name(path.name + f".bak.before_jpn_remaining_{stamp}")
    shutil.copy2(path, backup)
    path.write_bytes(text.encode("utf-16"))
    print(f"wrote {path} ({len(original)} -> {len(text)} chars), backup={backup}")


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for name, replacements in REPLACEMENTS.items():
        path = JPN / name
        if not path.is_file():
            raise FileNotFoundError(path)
        patch_file(path, replacements, stamp)


if __name__ == "__main__":
    main()
