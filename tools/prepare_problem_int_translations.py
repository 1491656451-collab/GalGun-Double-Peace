from __future__ import annotations

import json
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from translate_system_ints import decode_int, TECHNICAL_VALUE_RE

SOURCE_ROOT = Path(r"D:\GALGUNVV\steam\GG2Game\Localization\INT")
WORK_ROOT = Path(r"D:\GALGUNVV\work\system_int_translation")
OLD_CACHE = json.loads((WORK_ROOT / "translation_by_source.json").read_text(encoding="utf-8-sig"))
NEW_CACHE = json.loads((WORK_ROOT / "full_translations_source_deepl.json").read_text(encoding="utf-8-sig"))
OUT = WORK_ROOT / "problem_sources.json"
TARGET_FILES = {
    "CommonSet.int", "CommonSet_Eng.INT", "DemoCom.int", "DemoCom_ENG.int",
    "GG2Game.int", "GG2GirlDatas.int", "GG2GirlDatas_Eng.int",
    "levelList.int", "levelList_Eng.INT", "Sns.int", "Sns_ENG.int",
}
QUOTED_RE = re.compile(r'"((?:\\.|[^"\\])*)"')
COMMON_WORDS = re.compile(
    r"\b(?:the|and|you|your|i|we|me|my|to|of|for|is|are|no|let|so|what|"
    r"oh|hey|thank|please|really|again|can|will|have|with|from|this|that|"
    r"homework|memory|senpai|houdai|chan|san)\b",
    re.I,
)

def candidate_problem(source: str, translated: str | None) -> bool:
    if not re.search(r"[A-Za-z]{3,}", source):
        return False
    if TECHNICAL_VALUE_RE.fullmatch(source):
        return False
    low = source.lower()
    if any(x in low for x in (".umap", "soundcue'", "package'", "texture2d'", "additioncostume", "additionitem")):
        return False
    if translated is None or translated == source:
        return True
    words = re.findall(r"[A-Za-z]{3,}", source)
    return len(words) >= 4 and bool(COMMON_WORDS.search(translated))

def main() -> None:
    sources: dict[str, list[str]] = {}
    for path in sorted(SOURCE_ROOT.iterdir()):
        if path.name not in TARGET_FILES or not path.is_file():
            continue
        for match in QUOTED_RE.finditer(decode_int(path)):
            value = match.group(1)
            if value:
                sources.setdefault(value, []).append(path.name)
    result = []
    for source, files in sources.items():
        translated = NEW_CACHE.get(source, OLD_CACHE.get(source))
        if candidate_problem(source, translated):
            result.append({"source": source, "files": files, "previous": translated})
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"problem_sources": len(result), "output": str(OUT)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
