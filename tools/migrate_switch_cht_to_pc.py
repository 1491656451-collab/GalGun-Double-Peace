from __future__ import annotations

import argparse
import collections
import functools
import json
import re
from pathlib import Path

ROOT = Path(r"D:\GALGUNVV")
SOURCE_JSON = ROOT / "work" / "switch_cht_texts" / "all_switch_cht_texts_clean.json"
INT_ROOT = ROOT / "steam" / "GG2Game" / "Localization" / "INT"
DEFAULT_PATCH_ROOT = ROOT / "work" / "pc_cht_patch" / "GG2Game" / "Localization" / "INT"
DEFAULT_REPORT = ROOT / "work" / "pc_cht_patch" / "migration_report.json"
DEFAULT_WORDS = ROOT / "work" / "switch_cht_texts" / "UsedWordsListCHT.txt"
DEFAULT_WORDS_REPORT = ROOT / "work" / "switch_cht_texts" / "UsedWordsListCHT.report.json"

TEXT_RE = re.compile(r'Text="((?:\\.|[^"\\])*)"')
NAME_RE = re.compile(r'Name="((?:\\.|[^"\\])*)"')
FORMAT_END_RE = re.compile(r'(Format\[0\]=\([^)]*?\bEnd=)(-?\d+)')


def norm_name(value: str) -> str:
    return "".join(ch for ch in value if ch.isalnum())


def decode_utf16(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xff\xfe"):
        data = data[2:]
    return data.decode("utf-16le", errors="replace")


def encode_utf16(value: str) -> bytes:
    return b"\xff\xfe" + value.encode("utf-16le")


def field_value(line: str, regex: re.Pattern[str]) -> str:
    m = regex.search(line)
    return m.group(1) if m else ""


def replace_field(line: str, field: str, value: str) -> str:
    # These resources currently contain no quotes/backslashes in text. Keep the
    # escaping here so the generated patch remains safe if a future line does.
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    pattern = re.compile(rf'({field}=")((?:\\.|[^"\\])*)(")')
    if pattern.search(line):
        return pattern.sub(lambda m: m.group(1) + value + m.group(3), line, count=1)
    return line


def text_lines(value: str) -> list[str]:
    return [line for line in value.splitlines() if line.startswith("Texts[")]


def collect_name_candidates(source: dict) -> set[str]:
    all_strings = [s for item in source.values() for s in item.get("strings", [])]
    counts = collections.Counter(all_strings)
    # Repeated short strings are overwhelmingly character names. Exclude the
    # common debug/result labels, which otherwise look like names.
    excluded = {"大成功", "成功", "失敗", "沒問題了"}
    candidates = {s for s, count in counts.items() if count >= 2 and s not in excluded}
    for item in source.values():
        for pair in item.get("pairs", []):
            name = pair.get("name", "")
            if name and (" " in name or name in {"？？？", "峰大小子", "峰大　", "女神"}):
                candidates.add(name)
    return candidates - excluded


def build_fields(template_lines: list[str]):
    fields = []
    seen_texts: set[str] = set()
    expected_names: set[str] = set()
    for line_index, line in enumerate(template_lines):
        text = field_value(line, TEXT_RE)
        name = field_value(line, NAME_RE)
        # Include empty Text slots: some Switch maps have real selection strings
        # where the PC file currently has an empty SELECT slot.
        fields.append((line_index, "T", text, text in seen_texts))
        if text:
            seen_texts.add(text)
        if name and name != "NONE":
            fields.append((line_index, "N", name, False))
            expected_names.add(name)
    return fields, expected_names


def align(source_strings: list[str], target_lines: list[str], template_lines: list[str], global_names: set[str]):
    fields, expected_names = build_fields(template_lines)
    per_name = {name: {s for s in global_names if norm_name(s) == norm_name(name)} for name in expected_names}
    # Add one-off names from this map when their normalized form matches the
    # corresponding simplified template name.
    local_pair_names = set()
    source_item = None
    for item in []:
        source_item = item
    # target/template name aliases are supplied by the caller through the
    # global candidate set; exact CHT names are also covered below in the
    # caller's local-name augmentation.

    n_source = len(source_strings)

    @functools.lru_cache(maxsize=None)
    def solve(field_index: int, source_index: int):
        if field_index == len(fields):
            if source_index == n_source:
                return (0, ())
            return (1000 + (n_source - source_index), ())

        line_index, kind, key, is_repeat = fields[field_index]
        options = []
        if kind == "T":
            if source_index < n_source:
                cost, path = solve(field_index + 1, source_index + 1)
                options.append((cost, (("consume", line_index, kind, source_index),) + path))
            if key and is_repeat:
                cost, path = solve(field_index + 1, source_index)
                options.append((cost + 1, (("reuse", line_index, kind, None),) + path))
            if not key:
                cost, path = solve(field_index + 1, source_index)
                options.append((cost, (("skip", line_index, kind, None),) + path))
            if not options:
                cost, path = solve(field_index + 1, source_index)
                options.append((cost + 50, (("missing", line_index, kind, None),) + path))
        else:
            accepted = per_name.get(key, set())
            if source_index < n_source and (source_strings[source_index] in accepted or source_strings[source_index] in global_names):
                cost, path = solve(field_index + 1, source_index + 1)
                options.append((cost, (("consume", line_index, kind, source_index),) + path))
            cost, path = solve(field_index + 1, source_index)
            options.append((cost + 2, (("skip", line_index, kind, None),) + path))
        return min(options, key=lambda item: item[0])

    cost, path = solve(0, 0)
    assignments: dict[tuple[int, str], str] = {}
    text_by_source_key: dict[str, str] = {}
    for op, line_index, kind, source_index in path:
        if op == "consume":
            value = source_strings[source_index]
            assignments[(line_index, kind)] = value
            if kind == "T":
                text_by_source_key.setdefault(field_value(template_lines[line_index], TEXT_RE), value)
        elif op == "reuse":
            key = field_value(template_lines[line_index], TEXT_RE)
            if key in text_by_source_key:
                assignments[(line_index, kind)] = text_by_source_key[key]
        elif op == "skip" and kind == "N":
            # An omitted Switch speaker name should not leave a wrong PC name.
            assignments[(line_index, kind)] = ""

    consumed = sum(1 for op, *_ in path if op == "consume")
    reused = sum(1 for op, *_ in path if op == "reuse")
    skipped_text = sum(1 for op, _, kind, _ in path if op == "skip" and kind == "T")
    skipped_name = sum(1 for op, _, kind, _ in path if op == "skip" and kind == "N")
    missing = sum(1 for op, *_ in path if op == "missing")
    return assignments, {
        "cost": cost,
        "source_strings": n_source,
        "consumed": consumed,
        "reused_duplicate_texts": reused,
        "skipped_empty_pc_text_slots": skipped_text,
        "skipped_names": skipped_name,
        "missing_texts": missing,
        "leftover_source_strings": max(0, n_source - consumed),
    }


def update_format_end(line: str, old_text: str, new_text: str) -> str:
    if not old_text or old_text == new_text:
        return line
    old_len = len(old_text)
    new_len = len(new_text)
    def repl(match: re.Match[str]) -> str:
        old_end = int(match.group(2))
        if old_end == old_len:
            return match.group(1) + str(new_len)
        return match.group(0)
    return FORMAT_END_RE.sub(repl, line, count=1)


def patch_file(target_path: Path, template_path: Path, source_item: dict) -> tuple[str, dict]:
    target_text = decode_utf16(target_path)
    target_lines = target_text.splitlines(keepends=True)
    target_text_indices = [i for i, line in enumerate(target_lines) if line.startswith("Texts[")]
    target_text_values = [target_lines[i].rstrip("\r\n") for i in target_text_indices]

    global_names = patch_file.global_names  # type: ignore[attr-defined]
    assignments, stats = align(source_item.get("strings", []), target_text_values, target_text_values, global_names)
    for local_index, absolute_index in enumerate(target_text_indices):
        line = target_lines[absolute_index].rstrip("\r\n")
        old_text = field_value(line, TEXT_RE)
        if (local_index, "T") in assignments:
            line = replace_field(line, "Text", assignments[(local_index, "T")])
            line = update_format_end(line, old_text, assignments[(local_index, "T")])
        if (local_index, "N") in assignments:
            line = replace_field(line, "Name", assignments[(local_index, "N")])
        newline = "\r\n" if target_lines[absolute_index].endswith("\r\n") else "\n"
        target_lines[absolute_index] = line + newline
    stats["status"] = "ok" if stats["missing_texts"] == 0 and stats["leftover_source_strings"] == 0 else "partial"
    return "".join(target_lines), stats


def make_word_list(source: dict, path: Path, report_path: Path) -> dict:
    chars = set()
    text_count = 0
    for item in source.values():
        for value in item.get("strings", []):
            text_count += 1
            chars.update(value)
    ordered = "".join(sorted(chars, key=ord))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ordered + "\n", encoding="utf-8")
    stats = {
        "source_map_files": len(source),
        "source_string_values": text_count,
        "unique_characters": len(chars),
        "han_characters": sum(1 for c in chars if "\u3400" <= c <= "\u9fff"),
        "non_ascii_characters": sum(1 for c in chars if ord(c) > 127),
        "output": str(path),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write patched _ENG.int files into the Steam folder")
    parser.add_argument("--patch-root", type=Path, default=DEFAULT_PATCH_ROOT)
    parser.add_argument("--target-suffix", default="_ENG", help="target file suffix before .int; use empty string for base INT files")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    source = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    words_stats = make_word_list(source, DEFAULT_WORDS, DEFAULT_WORDS_REPORT)
    global_names = collect_name_candidates(source)
    patch_file.global_names = global_names  # type: ignore[attr-defined]

    report = {"mode": "apply" if args.apply else "preview", "target_suffix": args.target_suffix, "word_list": words_stats, "files": []}
    args.patch_root.mkdir(parents=True, exist_ok=True)
    for map_name, source_item in sorted(source.items()):
        base = Path(map_name).stem.removesuffix("_map")
        target = INT_ROOT / f"{base}{args.target_suffix}.int"
        template = INT_ROOT / f"{base}.int"
        if not target.exists() or not template.exists():
            report["files"].append({"map": map_name, "status": "missing_target_or_template", "target": str(target), "template": str(template)})
            continue
        patched_text, stats = patch_file(target, template, source_item)
        stats.update({"map": map_name, "target": str(target)})
        report["files"].append(stats)
        if stats.get("status") in {"ok", "partial"}:
            relative = target.relative_to(INT_ROOT)
            out = args.patch_root / relative
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(encode_utf16(patched_text))
            if args.apply:
                backup = target.with_suffix(target.suffix + ".bak.switch_cht")
                if not backup.exists():
                    backup.write_bytes(target.read_bytes())
                target.write_bytes(encode_utf16(patched_text))

    report["summary"] = {
        "files": len(report["files"]),
        "ok": sum(1 for x in report["files"] if x.get("status") == "ok"),
        "partial": sum(1 for x in report["files"] if x.get("status") == "partial"),
        "failed": sum(1 for x in report["files"] if x.get("status") not in {"ok", "partial"}),
        "patched_root": str(args.patch_root),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    print(json.dumps(words_stats, ensure_ascii=False))


if __name__ == "__main__":
    main()


