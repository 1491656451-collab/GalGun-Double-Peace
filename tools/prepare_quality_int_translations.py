from __future__ import annotations

import json
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from translate_system_ints import decode_int, TECHNICAL_VALUE_RE

SOURCE_ROOT = Path(r"D:\GALGUNVV\steam\GG2Game\Localization\INT")
WORK_ROOT = Path(r"D:\GALGUNVV\work\system_int_translation")
OLD = json.loads((WORK_ROOT / "translation_by_source.json").read_text(encoding="utf-8-sig"))
FULL = json.loads((WORK_ROOT / "full_translations_source_verified.json").read_text(encoding="utf-8"))
PROBLEM = json.loads((WORK_ROOT / "problem_translations_verified.json").read_text(encoding="utf-8"))
OUT = WORK_ROOT / "quality_sources.json"
TARGET_FILES = {
    "CommonSet.int", "CommonSet_Eng.INT", "DemoCom.int", "DemoCom_ENG.int",
    "GG2Game.int", "GG2GirlDatas.int", "GG2GirlDatas_Eng.int",
    "levelList.int", "levelList_Eng.INT", "Sns.int", "Sns_ENG.int",
}
QUOTED_RE = re.compile(r'"((?:\\.|[^"\\])*)"')
BAD_WORDS = re.compile(
    r"(?<![A-Za-z])(?:I|let|ummm|so|no|loss|memory|that|the|and|you|your|with|"
    r"from|BOSS|RPG|Senpai|Shempai|seme|san|chan)(?![A-Za-z])",
    re.I,
)

def main() -> None:
    sources = {}
    for path in sorted(SOURCE_ROOT.iterdir()):
        if path.name not in TARGET_FILES or not path.is_file():
            continue
        for match in QUOTED_RE.finditer(decode_int(path)):
            value = match.group(1)
            if value:
                sources.setdefault(value, []).append(path.name)
    result = []
    for source, files in sources.items():
        translated = PROBLEM.get(source, FULL.get(source, OLD.get(source)))
        if (
            len(source) >= 40
            and len(re.findall(r"[A-Za-z]{3,}", source)) >= 4
            and translated
            and BAD_WORDS.search(translated)
        ):
            result.append({"source": source, "files": files, "previous": translated})
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"quality_sources": len(result), "output": str(OUT)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
