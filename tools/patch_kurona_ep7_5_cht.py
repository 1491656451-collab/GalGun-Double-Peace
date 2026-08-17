from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(r"D:\GALGUNVV")
REL = Path("GG2Game/Localization/INT/Kurona_ep7_5.int")
TARGETS = [
    ROOT / "steam" / REL,
    Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace") / REL,
]

ACTORS = {
    "くろな": "庫蘿娜",
    "ホウダイ": "峰大",
    "えころ": "艾可蘿",
}

PAIRS = [
    ("ううぅ…\n…きりんぐみーそふとりぃ…", "唔唔……\n……ＫＩＬＬＩＮＧ　ＭＥ\nＳＯＦＴＬＹ……"),
    ("あれ…くろな…\nどうしちゃったＤＥＡＴＨ…？", "咦……庫蘿娜……\n怎麼了ＤＥＡＴＨ……？"),
    ("よかった…\n元に戻ったんだね。", "太好了……\n妳恢復原狀了啊。"),
    ("うぅ…なんだか…カラダが\nホカホカするＤＥＡＴＨ…", "唔唔……總覺得……\n身體暖烘烘的ＤＥＡＴＨ……"),
    ("まだ、少しダークパワーが\n残っているようですね。", "看來黑暗能量好像\n還剩下一些呢。"),
    ("ホウダイ様、\nここはドキドキフィールドを使って\n余分なパワーを中和してあげましょう。", "峰大大人，\n這裡就用心跳力場\n中和多餘的能量吧。"),
    ("まさか、くろなに対して\n使うことになるなんて…", "沒想到竟然演變成了\n要對庫蘿娜使用的情況……"),
    ("うぅー、頼むＤＥＡＴＨ…ホウダイ。\nこのままじゃ、ホカホカして\n落ち着かないＤＥＡＴＨ…", "唔唔，拜託了ＤＥＡＴＨ……峰大。\n再這樣下去，我會一直暖烘烘的，\n無法冷靜ＤＥＡＴＨ……"),
    ("なーんか、お二人とも\n意外にいい感じですね？\n…まぁ、別にいいですけど。", "總覺得兩位氣氛意外地不錯？\n……嗯，是也沒關係啦。"),
    ("それでは、レッツ・デトックスです！\nドキドキフィールド展開っ！！", "那麼就來解毒吧！\n心跳力場展開！！"),
]


def patch(path: Path) -> None:
    raw = path.read_bytes()
    text = raw[2:].decode("utf-16le") if raw.startswith(bytes([0xff, 0xfe])) else raw.decode("cp932")
    if not path.with_suffix(path.suffix + ".bak.switch_cht").exists():
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak.switch_cht"))
    for old, new in PAIRS:
        # DemoScripts stores the dialogue with physical line breaks; the Text
        # object stores the same breaks as the UE3 /n escape.
        text = text.replace(old, new)
        text = text.replace(old.replace("\n", "/n"), new.replace("\n", "/n"))
    for old, new in ACTORS.items():
        text = text.replace(old, new)
    path.write_bytes(bytes([0xff, 0xfe]) + text.encode("utf-16le"))


for target in TARGETS:
    if not target.exists():
        raise FileNotFoundError(target)
    patch(target)
    print(target)
