from __future__ import annotations

import json
import shutil
from pathlib import Path

from translate_system_ints import INT_ROOT, decode_int, encode_int, load_translations, patch_text


WORK_ROOT = Path(r"D:\GALGUNVV\work\system_int_candidate")
GAME_INT_ROOT = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\Localization\INT")

# Use the English source for both locale variants so the runtime cannot fall
# back to an untranslated *_ENG resource.
SOURCE_FOR_TARGET = {
    "CommonSet.int": "CommonSet_Eng.INT",
    "CommonSet_Eng.INT": "CommonSet_Eng.INT",
    "DemoCom.int": "DemoCom_ENG.int",
    "DemoCom_ENG.int": "DemoCom_ENG.int",
    "GG2Game.int": "GG2Game.int",
    "GG2GirlDatas.int": "GG2GirlDatas_Eng.int",
    "GG2GirlDatas_Eng.int": "GG2GirlDatas_Eng.int",
    "levelList.int": "levelList_Eng.INT",
    "levelList_Eng.INT": "levelList_Eng.INT",
    "Sns.int": "Sns_ENG.int",
    "Sns_ENG.int": "Sns_ENG.int",
}


def main() -> None:
    translations = load_translations()
    output = WORK_ROOT / "INT"
    output.mkdir(parents=True, exist_ok=True)
    report = []

    for target_name, source_name in SOURCE_FOR_TARGET.items():
        source_path = INT_ROOT / source_name
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        source_text = decode_int(source_path)
        patched = patch_text(source_name, source_text, translations)
        target_path = GAME_INT_ROOT / target_name
        candidate_path = output / target_name
        candidate_path.write_bytes(encode_int(patched))
        report.append(
            {
                "target": target_name,
                "source": source_name,
                "candidate_bytes": candidate_path.stat().st_size,
                "existing_bytes": target_path.stat().st_size if target_path.exists() else None,
            }
        )

    (WORK_ROOT / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"files": len(report), "output": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
