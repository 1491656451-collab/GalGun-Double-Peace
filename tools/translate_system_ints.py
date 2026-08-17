from __future__ import annotations

import argparse
import ctypes
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(r"D:\GALGUNVV")
INT_ROOT = ROOT / "steam" / "GG2Game" / "Localization" / "INT"
GAME_INT_ROOT = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\Localization\INT")
WORK_ROOT = ROOT / "work" / "system_int_translation"
OPENCC_ROOT = ROOT / "work" / "opencc_runtime"
if OPENCC_ROOT.exists():
    sys.path.insert(0, str(OPENCC_ROOT))
try:
    from opencc import OpenCC
except ImportError:
    OpenCC = None
OPENCC_S2T = OpenCC("s2t") if OpenCC is not None else None

TARGET_SOURCES = {
    "CommonSet.int": "CommonSet_Eng.INT",
    "CommonSet_Eng.INT": "CommonSet_Eng.INT",
    "DemoCom.int": "DemoCom_ENG.int",
    "GG2Game.int": "GG2Game.int",
    "GG2GirlDatas.int": "GG2GirlDatas_Eng.int",
    "GG2GirlDatas_Eng.int": "GG2GirlDatas_Eng.int",
    "levelList.int": "levelList_Eng.INT",
    "levelList_Eng.INT": "levelList_Eng.INT",
    "Sns.int": "Sns_ENG.int",
}

QUOTED_RE = re.compile(r'"((?:\\.|[^"\\])*)"')
DISPLAY_FIELDS = {
    "Name",
    "Text",
    "hn",
    "txt",
    "firstName",
    "lastName",
    "club0",
    "club1",
    "profileText",
}
TECHNICAL_VALUE_RE = re.compile(
    r"^(?:[A-Za-z_][A-Za-z0-9_.'/-]*|SoundCue'.*'|[+-]?\d+(?:\.\d+)?|True|False|None)$"
)


def decode_int(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xff\xfe"):
        return data[2:].decode("utf-16le")
    return data.decode("cp932", errors="replace")


def encode_int(text: str) -> bytes:
    return b"\xff\xfe" + text.encode("utf-16le")


def to_traditional(text: str) -> str:
    if OPENCC_S2T is not None:
        return OPENCC_S2T.convert(text)
    return windows_s2t(text)

def windows_s2t(text: str) -> str:
    if not text:
        return text
    kernel32 = ctypes.windll.kernel32
    flags = 0x04000000  # LCMAP_TRADITIONAL_CHINESE
    needed = kernel32.LCMapStringEx("zh-TW", flags, text, len(text), None, 0, None, None, 0)
    if needed <= 0:
        return text
    buf = ctypes.create_unicode_buffer(needed)
    kernel32.LCMapStringEx("zh-TW", flags, text, len(text), buf, needed, None, None, 0)
    return buf.value


def build_official_translation_memory() -> dict[str, str]:
    memory: dict[str, str] = {}
    for backup in INT_ROOT.glob("*.bak.switch_cht"):
        current = Path(str(backup).removesuffix(".bak.switch_cht"))
        if not current.exists():
            continue
        source_matches = list(QUOTED_RE.finditer(decode_int(backup)))
        target_matches = list(QUOTED_RE.finditer(decode_int(current)))
        if len(source_matches) != len(target_matches):
            continue
        for source_match, target_match in zip(source_matches, target_matches):
            source = source_match.group(1)
            target = target_match.group(1)
            if source and target and source != target:
                memory.setdefault(source, target)
    return memory


def field_before(text: str, quote_start: int) -> str:
    prefix = text[max(0, quote_start - 40) : quote_start]
    match = re.search(r"([A-Za-z][A-Za-z0-9_]*)\s*=\s*$", prefix)
    return match.group(1) if match else ""


def extract_strings(filename: str, text: str, memory: dict[str, str]) -> list[dict]:
    result: list[dict] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for ordinal, match in enumerate(QUOTED_RE.finditer(line)):
            value = match.group(1)
            field = field_before(line, match.start())
            if not value or TECHNICAL_VALUE_RE.fullmatch(value):
                continue
            if filename.startswith("DemoCom") and field not in DISPLAY_FIELDS:
                continue
            if filename.startswith("Sns") and field not in {"hn", "txt", "Text", "Name"}:
                continue
            result.append(
                {
                    "id": f"{filename}:{line_no}:{ordinal}",
                    "file": filename,
                    "line": line_no,
                    "ordinal": ordinal,
                    "field": field,
                    "source": value,
                    "translation": memory.get(value, windows_s2t(value)),
                    "official_memory": value in memory,
                }
            )
    return result


def export_catalog() -> None:
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    memory = build_official_translation_memory()
    catalog: list[dict] = []
    for source_name in sorted(set(TARGET_SOURCES.values())):
        text = decode_int(INT_ROOT / source_name)
        catalog.extend(extract_strings(source_name, text, memory))
    (WORK_ROOT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    stats = {
        "entries": len(catalog),
        "unique_sources": len({item["source"] for item in catalog}),
        "official_memory_entries": len(memory),
        "official_memory_matches": sum(item["official_memory"] for item in catalog),
        "files": {},
    }
    for item in catalog:
        stats["files"][item["file"]] = stats["files"].get(item["file"], 0) + 1
    (WORK_ROOT / "catalog.report.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(stats, ensure_ascii=False))


def load_translations() -> dict[tuple[str, int, int], str]:
    catalog = json.loads((WORK_ROOT / "catalog.json").read_text(encoding="utf-8"))
    source_overrides_path = WORK_ROOT / "translation_by_source.json"
    source_overrides = (
        json.loads(source_overrides_path.read_text(encoding="utf-8-sig"))
        if source_overrides_path.exists()
        else {}
    )
    manual_overrides_path = WORK_ROOT / "manual_overrides.json"
    manual_overrides = (
        json.loads(manual_overrides_path.read_text(encoding="utf-8-sig"))
        if manual_overrides_path.exists()
        else {}
    )
    return {
        (item["file"], item["line"], item["ordinal"]): to_traditional(
            manual_overrides.get(
                item["source"], source_overrides.get(item["source"], item["translation"])
            )
        )
        for item in catalog
    }


def patch_text(source_name: str, text: str, translations: dict[tuple[str, int, int], str]) -> str:
    out: list[str] = []
    for line_no, line in enumerate(text.splitlines(keepends=True), 1):
        newline = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
        body = line[: -len(newline)] if newline else line
        matches = list(QUOTED_RE.finditer(body))
        for ordinal, match in reversed(list(enumerate(matches))):
            translated = translations.get((source_name, line_no, ordinal))
            if translated is None:
                continue
            translated = translated.replace("\\", "\\\\").replace('"', '\\"')
            body = body[: match.start(1)] + translated + body[match.end(1) :]
        if source_name.startswith("Sns"):
            body = update_sns_text_lengths(body)
        out.append(body + newline)
    return "".join(out)


def unescape_ue(value: str) -> str:
    return value.replace("/n", "\n").replace('\\"', '"').replace("\\\\", "\\")


def update_sns_text_lengths(line: str) -> str:
    pattern = re.compile(
        r'(txt="((?:\\.|[^"\\])*)",tcfl\[0\]=\(sPos=(\d+),ePos=)(\d+)'
    )

    def repl(match: re.Match[str]) -> str:
        start = int(match.group(3))
        end = start + len(unescape_ue(match.group(2)))
        return match.group(1) + str(end)

    return pattern.sub(repl, line)


def apply_catalog() -> None:
    translations = load_translations()
    for target_name, source_name in TARGET_SOURCES.items():
        source_text = decode_int(INT_ROOT / source_name)
        patched = patch_text(source_name, source_text, translations)
        for root in (INT_ROOT, GAME_INT_ROOT):
            target = root / target_name
            if not target.exists():
                continue
            backup = target.with_suffix(target.suffix + ".bak.system_cht")
            if not backup.exists():
                shutil.copy2(target, backup)
            target.write_bytes(encode_int(patched))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("export", "apply"))
    args = parser.parse_args()
    if args.command == "export":
        export_catalog()
    else:
        apply_catalog()


if __name__ == "__main__":
    main()
