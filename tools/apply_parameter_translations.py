from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil


GAME = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace")
LOCALIZATION = GAME / "GG2Game" / "Localization" / "INT"

TARGETS = [
    LOCALIZATION / "Sns_ENG.int",
    LOCALIZATION / "Tutorial_Destiny.int",
    LOCALIZATION / "Tutorial_Destiny_ENG.int",
]

REPLACEMENTS = {
    "智力,/n運動, 時尚, and 色氣": "智力、體能、風格和好色程度",
    "色氣 too??": "好色也算嗎？",
    "學業、運動、打扮、好色": "智力、體能、風格、好色",
}


def patch(path: Path, stamp: str) -> None:
    raw = path.read_bytes()
    text = raw.decode("utf-16")
    changed = 0
    for source, target in REPLACEMENTS.items():
        count = text.count(source)
        if count:
            text = text.replace(source, target)
            changed += count
            print(f"{path.name}: {source!r} -> {target!r} ({count})")
    if not changed:
        print(f"{path.name}: no parameter text changes")
        return
    backup = path.with_name(path.name + f".bak.before_parameter_labels_{stamp}")
    shutil.copy2(path, backup)
    path.write_bytes(text.encode("utf-16"))
    print(f"backup={backup}")


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for path in TARGETS:
        if not path.is_file():
            raise FileNotFoundError(path)
        patch(path, stamp)


if __name__ == "__main__":
    main()
