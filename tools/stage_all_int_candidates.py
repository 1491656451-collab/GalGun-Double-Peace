from __future__ import annotations

import json
import re
from pathlib import Path

from translate_system_ints import decode_int, encode_int, to_traditional, update_sns_text_lengths


GAME_INT_ROOT = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\Localization\INT")
WORK_ROOT = Path(r"D:\GALGUNVV\work\int_all_candidate\INT")
CACHE_PATH = Path(r"D:\GALGUNVV\work\system_int_translation\translation_by_source.json")
MANUAL_PATH = Path(r"D:\GALGUNVV\work\system_int_translation\manual_overrides.json")
QUOTED_RE = re.compile(r'"((?:\\.|[^"\\])*)"')


def main() -> None:
    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8-sig"))
    manual = json.loads(MANUAL_PATH.read_text(encoding="utf-8-sig")) if MANUAL_PATH.exists() else {}
    replacements = {source: to_traditional(manual.get(source, translated)) for source, translated in cache.items()}
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    report = []

    for path in sorted(GAME_INT_ROOT.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".int" or ".bak." in path.name:
            continue
        source_text = decode_int(path)
        changed = 0

        def replace(match: re.Match[str]) -> str:
            nonlocal changed
            source = match.group(1)
            translated = replacements.get(source)
            if translated is None or translated == source:
                return match.group(0)
            changed += 1
            escaped = translated.replace("\\", "\\\\").replace('"', '\\"')
            return '"' + escaped + '"'

        patched = QUOTED_RE.sub(replace, source_text)
        if path.name.lower().startswith("sns"):
            patched = "".join(update_sns_text_lengths(line) for line in patched.splitlines(keepends=True))

        candidate = WORK_ROOT / path.name
        candidate.write_bytes(encode_int(patched))
        report.append(
            {
                "file": path.name,
                "changed_values": changed,
                "existing_bytes": path.stat().st_size,
                "candidate_bytes": candidate.stat().st_size,
            }
        )

    (WORK_ROOT.parent / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "files": len(report),
        "changed_files": sum(item["changed_values"] > 0 for item in report),
        "changed_values": sum(item["changed_values"] for item in report),
        "output": str(WORK_ROOT),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
