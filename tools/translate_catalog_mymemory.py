from __future__ import annotations

import argparse
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(r"D:\GALGUNVV\work\system_int_translation")
CATALOG = ROOT / "catalog.json"
OUTPUT = ROOT / "translation_by_source.json"
DELIMITER = "ZXQSEPZXQ"
MAX_QUERY_CHARS = 430


def source_language(text: str) -> str | None:
    if any("\u3040" <= ch <= "\u30ff" for ch in text):
        return "ja"
    latin = sum(ch.isascii() and ch.isalpha() for ch in text)
    han = sum("\u3400" <= ch <= "\u9fff" for ch in text)
    if latin >= 2 and latin > han:
        return "en"
    return None


def protect(text: str) -> str:
    return (
        text.replace("/n", "ZXQLINEZXQ")
        .replace("\\n", "ZXQBACKLINEZXQ")
        .replace('\\"', "ZXQQUOTEZXQ")
    )


def restore(text: str) -> str:
    return (
        text.replace("ZXQLINEZXQ", "/n")
        .replace("ZXQBACKLINEZXQ", "\\n")
        .replace("ZXQQUOTEZXQ", '\\"')
    )


def request_translation(texts: list[str], language: str) -> list[str]:
    query = f"\n{DELIMITER}\n".join(protect(text) for text in texts)
    params = urllib.parse.urlencode(
        {"q": query, "langpair": f"{language}|zh-TW"}
    )
    request = urllib.request.Request(
        "https://api.mymemory.translated.net/get?" + params,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        payload = json.load(response)
    translated = html.unescape(payload["responseData"]["translatedText"])
    parts = re.split(rf"\s*{DELIMITER}\s*", translated)
    if len(parts) != len(texts):
        raise RuntimeError(f"Batch split mismatch: {len(parts)} != {len(texts)}")
    return [restore(part.strip()) for part in parts]


def make_batches(items: list[str]) -> list[list[str]]:
    result: list[list[str]] = []
    current: list[str] = []
    current_size = 0
    separator_size = len(DELIMITER) + 2
    for item in items:
        item_size = len(protect(item))
        extra = item_size + (separator_size if current else 0)
        if current and current_size + extra > MAX_QUERY_CHARS:
            result.append(current)
            current = []
            current_size = 0
        current.append(item)
        current_size += item_size + (separator_size if len(current) > 1 else 0)
    if current:
        result.append(current)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-batches", type=int, default=0)
    parser.add_argument("--delay", type=float, default=0.35)
    args = parser.parse_args()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    cache = json.loads(OUTPUT.read_text(encoding="utf-8-sig")) if OUTPUT.exists() else {}
    unique = list(dict.fromkeys(item["source"] for item in catalog))
    processed_batches = 0

    for language in ("en", "ja"):
        pending = [
            text
            for text in unique
            if text not in cache and source_language(text) == language
        ]
        batches = make_batches(pending)
        for index, batch in enumerate(batches, 1):
            if args.max_batches and processed_batches >= args.max_batches:
                print(json.dumps({"cached": len(cache), "remaining": len(pending)}, ensure_ascii=False))
                return
            last_error: Exception | None = None
            for attempt in range(4):
                try:
                    translations = request_translation(batch, language)
                    for source, translated in zip(batch, translations):
                        cache[source] = translated
                    OUTPUT.write_text(
                        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                    last_error = None
                    break
                except Exception as error:
                    last_error = error
                    cooldown = 65 if getattr(error, "code", None) == 429 else 2.0 * (attempt + 1)
                    if cooldown == 65:
                        print("rate limited; cooling down 65 seconds", flush=True)
                    time.sleep(cooldown)
            if last_error is not None:
                raise last_error
            processed_batches += 1
            print(language, index, "/", len(batches), "cached", len(cache), flush=True)
            time.sleep(args.delay)

    print(json.dumps({"cached": len(cache), "status": "complete"}, ensure_ascii=False))


if __name__ == "__main__":
    main()


