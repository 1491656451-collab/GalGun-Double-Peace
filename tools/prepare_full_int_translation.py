from __future__ import annotations

import json
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from translate_system_ints import decode_int, TECHNICAL_VALUE_RE


SOURCE_ROOT = Path(r"D:\GALGUNVV\steam\GG2Game\Localization\INT")
WORK_ROOT = Path(r"D:\GALGUNVV\work\system_int_translation")
CACHE_PATH = WORK_ROOT / "translation_by_source.json"
OUT_PATH = WORK_ROOT / "full_missing_sources.json"

TARGET_FILES = {
    "CommonSet.int",
    "CommonSet_Eng.INT",
    "DemoCom.int",
    "DemoCom_ENG.int",
    "GG2Game.int",
    "GG2GirlDatas.int",
    "GG2GirlDatas_Eng.int",
    "levelList.int",
    "levelList_Eng.INT",
    "Sns.int",
    "Sns_ENG.int",
}
QUOTED_RE = re.compile(r'"((?:\\.|[^"\\])*)"')


def is_translatable(value: str) -> bool:
    if not value or not re.search(r"[A-Za-z]{3,}", value):
        return False
    if TECHNICAL_VALUE_RE.fullmatch(value):
        return False
    lower = value.lower()
    if any(token in lower for token in (".umap", "soundcue'", "package'", "texture2d'")):
        return False
    return True


def main() -> None:
    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8-sig"))
    sources: dict[str, list[str]] = {}
    for path in sorted(SOURCE_ROOT.iterdir()):
        if path.name not in TARGET_FILES or not path.is_file():
            continue
        for match in QUOTED_RE.finditer(decode_int(path)):
            value = match.group(1)
            if is_translatable(value):
                sources.setdefault(value, []).append(path.name)

    missing = [
        {"source": source, "files": files}
        for source, files in sources.items()
        if source not in cache
    ]
    OUT_PATH.write_text(json.dumps(missing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "target_files": len(TARGET_FILES),
        "unique_translatable_sources": len(sources),
        "already_cached": len(sources) - len(missing),
        "missing": len(missing),
        "output": str(OUT_PATH),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
