from __future__ import annotations

import json
import re
from pathlib import Path

from translate_system_ints import decode_int, encode_int, to_traditional, update_sns_text_lengths


GAME_INT_ROOT = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\Localization\INT")
SOURCE_INT_ROOT = Path(r"D:\GALGUNVV\steam\GG2Game\Localization\INT")
WORK_ROOT = Path(r"D:\GALGUNVV\work\int_all_candidate_v3\INT")
CACHE_PATH = Path(r"D:\GALGUNVV\work\system_int_translation\translation_by_source.json")
FULL_CACHE_PATH = Path(r"D:\GALGUNVV\work\system_int_translation\full_translations_source_verified.json")
PROBLEM_CACHE_PATH = Path(r"D:\GALGUNVV\work\system_int_translation\problem_translations_verified.json")
QUALITY_CACHE_PATH = Path(r"D:\GALGUNVV\work\system_int_translation\quality_translations_verified.json")
MANUAL_PATH = Path(r"D:\GALGUNVV\work\system_int_translation\manual_overrides_clean.json")
QUOTED_RE = re.compile(r'"((?:\\.|[^"\\])*)"')


def main() -> None:
    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8-sig"))
    if FULL_CACHE_PATH.exists():
        cache.update(json.loads(FULL_CACHE_PATH.read_text(encoding="utf-8-sig")))
    if PROBLEM_CACHE_PATH.exists():
        cache.update(json.loads(PROBLEM_CACHE_PATH.read_text(encoding="utf-8-sig")))
    if QUALITY_CACHE_PATH.exists():
        cache.update(json.loads(QUALITY_CACHE_PATH.read_text(encoding="utf-8-sig")))
    manual = json.loads(MANUAL_PATH.read_text(encoding="utf-8-sig")) if MANUAL_PATH.exists() else {}
    # Older extraction batches contained property-label fragments such as
    # "LocalizedTextDelete[0]=" as if they were quoted display strings. They
    # are not values; replacing them would remove the CR CR LF separators
    # required by UE3's localization parser.
    replacements = {
        source: to_traditional(manual.get(source, translated))
        for source, translated in cache.items()
        if not source.endswith("=") and "\r\r\n" not in source
    }
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    report = []
    source_based_files = {
        "CommonSet.int", "CommonSet_Eng.INT", "DemoCom.int", "DemoCom_ENG.int",
        "GG2Game.int", "GG2GirlDatas.int", "GG2GirlDatas_Eng.int",
        "levelList.int", "levelList_Eng.INT", "Sns.int", "Sns_ENG.int",
    }

    for path in sorted(GAME_INT_ROOT.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".int" or ".bak." in path.name:
            continue
        source_path = SOURCE_INT_ROOT / path.name if path.name in source_based_files else path
        raw = source_path.read_bytes()
        source_text = decode_int(source_path)
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
        if path.name.lower() == "gg2game.int":
            save_ui_overrides = {
                "LocalizedTextDelete": "刪除",
                "LocalizedTextShinobuRoute": "小忍路線",
                "LocalizedTextCommonRoute": "一般路線",
                "LocalizedTextCheckLoad": "確定要載入這個存檔嗎？",
                "LocalizedTextCheckDelete": "確定要刪除這個存檔嗎？",
            }
            for key, value in save_ui_overrides.items():
                patched = re.sub(
                    rf'({re.escape(key)}\[[01]\]=")[^"]*(")',
                    lambda match, value=value: match.group(1) + value + match.group(2),
                    patched,
                )
            patched = re.sub(
                r'(LocalizeTextNextEpisode=")[^"]*(")',
                r'\1下一章节\2',
                patched,
            )
            patched = re.sub(
                r'(LocalizeTextShop=")[^"]*(")',
                r'\1學院商店\2',
                patched,
            )
            patched = re.sub(
                r'(LocalizeTextTitle=")[^"]*(")',
                r'\1返回標題畫面\2',
                patched,
            )
        # Some older translated values used this temporary quote placeholder.
        patched = patched.replace(r"\\ZXQQUOTE", "").replace("ZXQQUOTE", "")
        if path.name.lower().startswith("sns"):
            patched = "".join(update_sns_text_lengths(line) for line in patched.splitlines(keepends=True))

        encoding = "utf-16le" if raw.startswith(b"\xff\xfe") else "cp932"
        skipped = False
        try:
            encoded = encode_int(patched) if encoding == "utf-16le" else patched.encode("cp932")
        except UnicodeEncodeError:
            # Japanese CP932 locale files cannot represent the new CHT glyphs.
            encoded = raw
            changed = 0
            skipped = True

        candidate = WORK_ROOT / path.name
        candidate.write_bytes(encoded)
        report.append({
            "file": path.name,
            "changed_values": changed,
            "skipped_unrepresentable": skipped,
            "existing_bytes": path.stat().st_size,
            "candidate_bytes": candidate.stat().st_size,
            "encoding": encoding,
        })

    (WORK_ROOT.parent / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "files": len(report),
        "changed_files": sum(item["changed_values"] > 0 for item in report),
        "changed_values": sum(item["changed_values"] for item in report),
        "skipped_files": sum(item["skipped_unrepresentable"] for item in report),
        "output": str(WORK_ROOT),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
