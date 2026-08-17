from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil


GAME_ROOT = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace")
LOCALIZATION = GAME_ROOT / "GG2Game" / "Localization" / "INT"
JPN_LOCALIZATION = GAME_ROOT / "GG2Game" / "Localization" / "JPN"

# These are the terms still present in the English SNS/tutorial resource.
REPLACEMENTS = {
    "Houdai Kudoki": "峯大",
    "Intelligence": "智力",
    "Athleticism": "運動",
    "Style": "時尚",
    "Lewdness": "色氣",
    "Academy Store": "學院商店",
}


def patch_file(path: Path, stamp: str) -> list[tuple[str, int]]:
    raw = path.read_bytes()
    text = raw.decode("utf-16")
    counts: list[tuple[str, int]] = []
    for source, target in REPLACEMENTS.items():
        count = text.count(source)
        if count:
            text = text.replace(source, target)
        counts.append((source, count))

    if not any(count for _, count in counts):
        return counts

    backup = path.with_name(path.name + f".bak.before_remaining_text_{stamp}")
    shutil.copy2(path, backup)
    path.write_bytes(text.encode("utf-16"))
    return counts


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    targets = [
        LOCALIZATION / "Sns_ENG.int",
        LOCALIZATION / "GG2Game.int",
        JPN_LOCALIZATION / "Sns_ENG.jpn",
    ]
    for path in targets:
        if not path.is_file():
            raise FileNotFoundError(path)
        counts = patch_file(path, stamp)
        print(path)
        for source, count in counts:
            print(f"  {source!r}: {count}")


if __name__ == "__main__":
    main()
