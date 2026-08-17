from __future__ import annotations

import re
from pathlib import Path


GAME = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace")
LOC = GAME / "GG2Game" / "Localization" / "INT"
OUT = Path(r"D:\GALGUNVV\work") / "girl_profiles_wrapped"
FILES = ("GG2GirlDatas.int", "GG2GirlDatas_Eng.int")
MAX_CHARS = 22


def wrap_value(value: str) -> str:
    parts = value.split("/n")
    wrapped = []
    for part in parts:
        if not part:
            wrapped.append(part)
            continue
        wrapped.extend(part[index : index + MAX_CHARS] for index in range(0, len(part), MAX_CHARS))
    return "/n".join(wrapped)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    total_changed = 0
    report = []
    pattern = re.compile(r'^(profileText=")([^"]*)(")$')
    for name in FILES:
        source = LOC / name
        text = source.read_text(encoding="utf-16")
        changed = 0
        output_lines = []
        for line in text.splitlines(keepends=True):
            newline = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
            body = line[: -len(newline)] if newline else line
            match = pattern.match(body)
            if match:
                value = match.group(2)
                new_value = wrap_value(value)
                if new_value != value:
                    changed += 1
                body = match.group(1) + new_value + match.group(3)
            output_lines.append(body + newline)
        target = OUT / name
        target.write_text("".join(output_lines), encoding="utf-16")
        total_changed += changed
        report.append({"file": name, "changed_profiles": changed})
    print({"total_changed": total_changed, "files": report})


if __name__ == "__main__":
    main()
