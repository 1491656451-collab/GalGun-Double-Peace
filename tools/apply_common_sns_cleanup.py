from pathlib import Path


LOC = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\Localization\INT")


def replace_in_utf16(path: Path, replacements: list[tuple[str, str]]) -> dict[str, int]:
    text = path.read_bytes().decode("utf-16")
    counts: dict[str, int] = {}
    for old, new in replacements:
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            counts[old] = count
    path.write_bytes(text.encode("utf-16"))
    return counts


def main() -> None:
    common_replacements = [
        ("昇降口前広場", "入口前廣場"),
        ("図書室", "圖書室"),
        ("保健室周辺", "保健室周邊"),
        ("敷料Rm 2", "材料室2"),
        ("櫻花之路 (PM)", "櫻花之路（下午）"),
        ("店長推薦CD", "店長推薦唱片"),
        ("VS忍", "對戰忍"),
        ("VS 埃科羅", "對戰埃科羅"),
        ("VS庫羅娜", "對戰庫羅娜"),
        ("VS帕塔科", "對戰帕塔科"),
    ]
    sns_replacements = [
        ("SAYAKA NITTA", "新田沙耶香"),
        ("ぱたこ", "天塚帕塔子"),
        ("Jag er ledsen……對不起，里昂，", "對不起，里昂，"),
        ("Houdai", "霍代"),
        ("Tsubomi", "綻"),
        ("Aki", "亞紀"),
        ("Rosie", "羅茜"),
        ("Mai-chan", "麻衣醬"),
        ("Kotobuki", "壽"),
        ("Pettanko", "平胸"),
        ("Kanko", "甘子"),
        ("Neneko", "貓貓"),
        ("Right", "來特"),
        ("SCRUNCHY", "髮圈"),
        ("Riko", "莉子"),
        ("Sayu", "紗由"),
        ("Ise", "伊勢"),
        ("Yuyu", "悠悠"),
        ("Ren", "倫"),
        ("Ringo", "林戈"),
        ("加油，琳！", "加油，倫！"),
        ("萊特", "來特"),
        ("凜", "琳"),
        ("Maya", "瑪雅"),
        ("Ho-nii", "霍尼"),
        ("HNNNNNNGH", "啊啊啊啊"),
        ("Barista", "咖啡師"),
        ("LOVEHEARTS", "愛心戀曲"),
        ("ZOOM", "縮放"),
        ("nclub", "n社團"),
        ("Mote-Mote", "多奇-多奇"),
    ]
    for name in ("CommonSet.int", "CommonSet_Eng.INT"):
        print(name, replace_in_utf16(LOC / name, common_replacements))
    for name in ("Sns.int", "Sns_ENG.int"):
        print(name, replace_in_utf16(LOC / name, sns_replacements))


if __name__ == "__main__":
    main()
