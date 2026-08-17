from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil


GAME = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace")
LOC = GAME / "GG2Game" / "Localization" / "INT"


def read_utf16(path: Path) -> str:
    return path.read_bytes().decode("utf-16")


def write_utf16(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-16"))


def set_indexed(text: str, field: str, index: int, value: str) -> str:
    pattern = re.compile(
        rf'({re.escape(field)}\[{index}\]\s*=\s*")((?:\\.|[^"\\])*)(")'
    )
    updated, count = pattern.subn(lambda m: m.group(1) + value + m.group(3), text)
    if count == 0:
        raise RuntimeError(f"missing {field}[{index}]")
    return updated


def patch_common_set(text: str) -> str:
    goods = {
        6: "無",
        16: "店長推薦遊戲",
        17: "店長推薦CD",
        18: "購物袋",
        19: "紙箱情書",
        20: "哥德貓情書",
        21: "愛心章魚燒",
        39: "告白板",
    }
    accessories = {
        0: "無",
        6: "手裏劍髮飾",
        10: "清潔拖把",
        11: "GEO髮飾",
        12: "遮陽帽",
        13: "紙箱頭套",
        14: "黑色貓耳",
        15: "扭結頭巾",
    }
    sns_items = {
        0: "作業本",
        11: "簽名板",
        14: "生火腿",
        25: "香蕉",
        34: "沙鈴",
        47: "排球",
        49: "假髮",
        53: "止痛貼布",
        62: "封印護符",
    }
    title_texts = {
        0: "純情", 1: "抖M", 2: "巨乳", 3: "平胸", 4: "眼鏡",
        5: "女教師", 6: "年上", 7: "年下", 8: "蘿莉", 9: "普通",
        10: "額頭", 11: "後腦", 12: "天使環", 13: "惡魔角", 14: "耳",
        15: "臉", 16: "眼睛", 17: "嘴巴", 18: "脖子", 19: "胸部",
        20: "乳溝", 21: "腰側", 22: "肚臍", 23: "腰腹", 24: "腰",
        25: "大腿", 26: "膝蓋", 27: "小腿", 28: "後頸", 29: "背部",
        30: "翅根", 31: "屁股", 32: "惡魔尾巴", 33: "大腿內側",
        34: "膝後", 35: "小腿肚", 36: "喜歡的人", 37: "獵人",
        38: "師父", 39: "魔人", 40: "王者", 41: "主人", 42: "神",
    }
    for index, value in goods.items():
        text = set_indexed(text, "m_girlGoodsTexts", index, value)
    for index, value in accessories.items():
        text = set_indexed(text, "m_girlAccessoryTexts", index, value)
    for index, value in sns_items.items():
        text = set_indexed(text, "m_snsItemTexts", index, value)
    for index, value in title_texts.items():
        text = set_indexed(text, "m_plTitleTexts", index, value)

    text = set_indexed(text, "m_scoreAttackTexts", 27, "新教學樓")
    text = set_indexed(text, "m_scoreAttackTexts", 36, "窗邊的忍")
    text = set_indexed(text, "m_crossSaveTexts", 47, "已登出PSN。")
    text = set_indexed(text, "m_crossSaveTexts", 49, "已斷開網路。")
    text = set_indexed(text, "m_common", 3, "舊夏制服")
    text = set_indexed(text, "m_common", 4, "二年級學生")

    text = re.sub(
        r'(m_girlClothesTexts\[\d+\]="DLC )(?:AdditionCostume|追加服裝)(\d+")',
        r'\1服裝\2',
        text,
    )
    text = re.sub(
        r'(m_girlGoodsTexts\[\d+\]="DLC )(?:AdditionItem|追加道具)(\d+")',
        r'\1道具\2',
        text,
    )
    text = re.sub(
        r'(m_girlAccessoryTexts\[\d+\]="DLC )(?:AdditionAccessory|追加配件|附加配件)(\d+")',
        r'\1配件\2',
        text,
    )

    simple_replacements = {
        'm_girlClothesTexts[15]="Misakimori"': 'm_girlClothesTexts[15]="三崎"',
        'm_girlClothesTexts[45]="Prisoner"': 'm_girlClothesTexts[45]="犯人"',
        'm_girlAccessoryTexts[2]="INSIDE-chan 的配件"': 'm_girlAccessoryTexts[2]="INSIDE配件"',
        'm_girlAccessoryTexts[3]="Misakimori 的配件"': 'm_girlAccessoryTexts[3]="三崎配件"',
        'm_common[2]="Misakimori制服"': 'm_common[2]="三崎制服"',
        'm_shitagiTexts[3]="Polka Dot套裝"': 'm_shitagiTexts[3]="波點套裝"',
        'm_snsItemTexts[6]="Z \'Gox模型"': 'm_snsItemTexts[6]="Z\'Gox模型"',
        'm_snsItemTexts[22]="Mountain o \'papers"': 'm_snsItemTexts[22]="山上紙張"',
        'm_plGameOverTexts[14]="Senpai直接上蜂巢了！"': 'm_plGameOverTexts[14]="學長直接上蜂窩了！"',
        'm_plGameOverTexts[39]="呵呵，我們要善良、體面、純潔！"': 'm_plGameOverTexts[39]="呵呵，我們要善良、體面、純潔！"',
    }
    for source, target in simple_replacements.items():
        if source in text:
            text = text.replace(source, target)

    text = text.replace("kamizono", "神園")
    text = text.replace("Doki-Doki", "心動")
    text = text.replace("Houdai", "峯大")
    text = text.replace("Ufu", "呵呵")
    text = text.replace("Riina的相機", "莉娜相機")
    return text


def patch_game(text: str) -> str:
    text = text.replace('EpisodeFinalText="FINAL"', 'EpisodeFinalText="最終"')
    text = text.replace("Good Ending", "好結局")
    text = text.replace("True Ending", "真結局")
    text = text.replace("Bad Ending", "壞結局")
    text = text.replace('Titles[50]="Patako Ending"', 'Titles[50]="帕塔子 結局"')
    text = text.replace('Titles[51]="Patako Ending"', 'Titles[51]="帕塔子 結局"')
    text = text.replace('Titles[52]="Aoi Ending"', 'Titles[52]="葵 結局"')
    text = text.replace('Titles[53]="Aoi Ending"', 'Titles[53]="葵 結局"')
    text = text.replace('Titles[56]="Gallery 已全部完成！"', 'Titles[56]="畫廊已全部完成！"')
    text = text.replace('Titles[57]="Gallery 已全部完成！"', 'Titles[57]="畫廊已全部完成！"')
    text = set_indexed(text, "LT_ScreenVsyncSettingText", 0, "開啟")
    text = set_indexed(text, "LT_ScreenVsyncSettingText", 1, "關閉")
    months = {
        "Jan": "一月", "Feb": "二月", "Mar": "三月", "Apr": "四月",
        "May": "五月", "Jun": "六月", "Jul": "七月", "Aug": "八月",
        "Sep": "九月", "Oct": "十月", "Nov": "十一月", "Dec": "十二月",
    }
    for source, target in months.items():
        text = text.replace(f'LocalizedText{source}[0]="{source}"', f'LocalizedText{source}[0]="{target}"')
    text = set_indexed(text, "LocalizedTextRouteFinal", 0, "最終")
    text = set_indexed(text, "LocalizedTextRouteFinal", 1, "最終")
    text = set_indexed(text, "LocalizedTextBeginner", 1, "初學者")
    text = set_indexed(text, "LocalizedTextExpert", 1, "專家")
    text = text.replace('LT_KeyBindingPreCheckPageDown[1]="【Page Down】/ 次へ"', 'LT_KeyBindingPreCheckPageDown[1]="【Page Down】/ 下一頁"')
    text = text.replace('LT_KeyBindingPreCheckCaption[1]="ボタン配置の初期化を行います。"', 'LT_KeyBindingPreCheckCaption[1]="將開始按鍵設定。"')
    text = text.replace('LT_KeyBindingSettingCaption[1]="入力してください。"', 'LT_KeyBindingSettingCaption[1]="請輸入。"')
    text = text.replace('LT_KeyBindingSettingBackSpace[1]="[Backspace] / Abort"', 'LT_KeyBindingSettingBackSpace[1]="【Back Space】/ 取消"')
    text = text.replace('LT_KeyBindingPreCheckBackSpace[1]="[Backspace] / Abort"', 'LT_KeyBindingPreCheckBackSpace[1]="【Back Space】/ 取消"')
    text = text.replace('LT_KeyBindingAfterCheckPageDown[1]="[Page Down] / Done"', 'LT_KeyBindingAfterCheckPageDown[1]="【Page Down】/ 完成"')
    text = re.sub(r'LT_KeyBindingAfterCheckBackSpace\[0\]="[^\r\n]*', 'LT_KeyBindingAfterCheckBackSpace[0]="【Back Space】/ 取消"', text)
    text = re.sub(r'LT_KeyBindingAfterCheckCaption\[0\]="[^\r\n]*', 'LT_KeyBindingAfterCheckCaption[0]="請按「完成」套用這些設定。"', text)
    text = text.replace('LT_KeyBindingAfterCheckCaption[1]="この設定で問題なければ完了してください。"', 'LT_KeyBindingAfterCheckCaption[1]="確認無誤後即可套用這些設定。"')
    return text


def patch_sns(text: str) -> str:
    values = [
        "怎麼會帶沙鈴來啊！",
        "得說服葵！",
        "我們要為體育祭製作LOVEHEARTS的新歌。",
        "可是葵那傢伙說想演奏桑巴。",
        "桑巴很棒！/n我得想辦法說服她！",
        "只有你會這麼說！",
        "去找她，對著她搖沙鈴！/n這樣應該有用！",
        "別再提桑巴了！",
        "有人有沙鈴嗎？/n喜歡卡拉OK的人也許有！/n去三年級教室找找看吧！",
        "我找到有沙鈴的人了！",
        "沙鈴交給我！/n我會讓現場熱鬧起來！",
        "這樣一來葵就不會再提桑巴了！",
        "那個討厭鬼！！",
    ]
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if not line.startswith("m_snsObjectList[45]="):
            continue
        cursor = 0

        def replace_txt(match: re.Match[str]) -> str:
            nonlocal cursor
            if cursor >= len(values):
                return match.group(0)
            value = values[cursor]
            cursor += 1
            return 'txt="' + value + '"'

        lines[index] = re.sub(r'txt="((?:\\.|[^"\\])*)"', replace_txt, line)
        if cursor != len(values):
            raise RuntimeError(f"unexpected SNS item 45 field count: {cursor}")
    return "".join(lines)


def patch_file(path: Path, transform, stamp: str) -> None:
    source = read_utf16(path)
    updated = transform(source)
    if updated == source:
        raise RuntimeError(f"no changes produced for {path.name}")
    backup = path.with_name(path.name + f".bak.before_static_completion_{stamp}")
    shutil.copy2(path, backup)
    write_utf16(path, updated)
    print(f"{path.name}: backup={backup} bytes={path.stat().st_size}")


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    patch_file(LOC / "CommonSet.int", patch_common_set, stamp)
    patch_file(LOC / "GG2Game.int", patch_game, stamp)
    patch_file(LOC / "GG2GirlDatas.int", lambda text: text.replace('club0="Eng"', 'club0="特殊"').replace('profileText="Eng"', 'profileText="特殊角色資料"'), stamp)
    patch_file(LOC / "Sns.int", patch_sns, stamp)


if __name__ == "__main__":
    main()
