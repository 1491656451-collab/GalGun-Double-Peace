from pathlib import Path


GAME_ROOT = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace")
PATCH_ROOT = Path(r"D:\GALGUNVV\GG2CNPatch_Distribution_Final_20260809")
LOCALIZATION = GAME_ROOT / "GG2Game/Localization/INT"


def normalize(text: str) -> str:
    replacements = {
        0x00B7: ".",
        0x2014: "-",
        0x2018: "'",
        0x2019: "'",
        0x201C: '"',
        0x201D: '"',
        0x2026: "...",
        0x2027: ".",
        0x203B: "*",
        0x2500: "-",
        0x2606: "*",
        0x266A: "~",
        0x3000: " ",
        0x3001: ",",
        0x3002: ".",
        0x300A: "<",
        0x300B: ">",
        0x300C: '"',
        0x300D: '"',
        0x300E: '"',
        0x300F: '"',
        0x3010: "[",
        0x3011: "]",
    }
    replacements.update({code: chr(code - 0xFEE0) for code in range(0xFF01, 0xFF5F)})
    return text.translate(replacements)


def process(path: Path) -> bool:
    text = path.read_bytes().decode("utf-16")
    lines = text.splitlines(keepends=True)
    updated = []
    changed = False
    for line in lines:
        if "DemoScripts" not in line:
            normalized = normalize(line)
        else:
            normalized = line
        changed |= normalized != line
        updated.append(normalized)
    if changed:
        path.write_text("".join(updated), encoding="utf-16")
    return changed


def main() -> None:
    for source in sorted(LOCALIZATION.glob("*.int")):
        if source.name.lower().startswith("staffcreditarchetype"):
            continue
        if process(source):
            patch = PATCH_ROOT / source.relative_to(GAME_ROOT)
            patch.parent.mkdir(parents=True, exist_ok=True)
            patch.write_bytes(source.read_bytes())
            print(f"normalized {source.name}")


if __name__ == "__main__":
    main()
