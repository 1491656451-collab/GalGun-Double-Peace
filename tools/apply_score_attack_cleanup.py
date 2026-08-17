from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil


PATH = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\Localization\INT\CommonSet.int")


def main() -> None:
    text = PATH.read_bytes().decode("utf-16")
    replacements = {17: "操場", 22: "游泳池"}
    for index, value in replacements.items():
        pattern = re.compile(rf'(m_scoreAttackTexts\[{index}\]\s*=\s*")((?:\\.|[^"\\])*)"')
        text, count = pattern.subn(lambda m: m.group(1) + value + '"', text)
        if count != 1:
            raise RuntimeError(f"expected one m_scoreAttackTexts[{index}], got {count}")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = PATH.with_name(PATH.name + f".bak.before_score_attack_cleanup_{stamp}")
    shutil.copy2(PATH, backup)
    PATH.write_bytes(text.encode("utf-16"))
    print(f"backup={backup}")


if __name__ == "__main__":
    main()
