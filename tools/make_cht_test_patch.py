from pathlib import Path
import shutil
src = Path(r"D:\GALGUNVV\steam\GG2Game\Localization\INT\Aoi_1_ENG.int")
outroot = Path(r"D:\GALGUNVV\test_patch_cht_aoi1")
loc = outroot / "GG2Game" / "Localization" / "INT"
cooked = outroot / "GG2Game" / "CookedPC"
loc.mkdir(parents=True, exist_ok=True)
cooked.mkdir(parents=True, exist_ok=True)
# Keep the existing font patch workflow, but use a small Traditional Chinese glyph set.
shutil.copy2(r"D:\GALGUNVV\work\cht_font_test_output\Startup_LOC_INT.cht_test.upk", cooked / "Startup_LOC_INT.upk")
text = src.read_text(encoding="utf-16")
repls = {
    "哦，峰大。/n你会来学园购买部，/n还真少见啊。": "喔，峰大。/n你會來學園購買部，/n還真少見啊。",
    "你们两个认识吗？": "你們兩個認識嗎？",
    "嗯，她是我同班同学。/n她在叫 LOVEHEARTS 的乐队里弹吉他，/n在学校里挺有名的。": "嗯，她是我同班同學。/n她在叫 LOVEHEARTS 的樂隊裡彈吉他，/n在學校裡挺有名的。",
    "她为了攒乐队活动资金，/n在这里打工。/n所以大家基本都认识她。": "她為了攢樂隊活動資金，/n在這裡打工。/n所以大家基本都認識她。",
    "而且葵好像也不受我的气场影响。/n难道她也是恶魔猎人？": "而且葵好像也不受我的氣場影響。/n難道她也是惡魔獵人？",
    "我还没仔细说明这部分呢。/n有时候，普通人也不会受到/n你的气场影响。": "我還沒仔細說明這部分呢。/n有時候，普通人也不會受到/n你的氣場影響。",
    "原因因人而异。/n有时是因为她非常讨厌你，/n有时则是因为她非常喜欢你。": "原因因人而異。/n有時是因為她非常討厭你，/n有時則是因為她非常喜歡你。",
    "两个极端啊？真麻烦。/n不过我当然更希望是后者。": "兩個極端啊？真麻煩。/n不過我當然更希望是後者。",
    "你刚才一直在自言自语吧……/n有点像我尊敬的那个学长。/n还挺帅的。": "你剛才一直在自言自語吧……/n有點像我尊敬的那個學長。/n還挺帥的。",
    "以前有段时间，那个学长也会像这样/n突然一个人说话。": "以前有段時間，那個學長也會像這樣/n突然一個人說話。",
    "她说的那个学长，/n听起来也不是一般人呢……": "她說的那個學長，/n聽起來也不是一般人呢……",
    "嗯，这所学校不知道为什么，/n怪人特别多。": "嗯，這所學校不知道為什麼，/n怪人特別多。",
    "所以……你要买什么？/n“What're ya buyin'?”": "所以……你要買什麼？/n“What're ya buyin'?”",
    'Name="艾可萝"': 'Name="艾可蘿"',
}
for a,b in repls.items():
    text = text.replace(a,b)
for name in ("Aoi_1_ENG.int", "Aoi_1.int"):
    (loc/name).write_text(text, encoding="utf-16")
readme = """GalGun Double Peace - small Traditional Chinese test patch\n\nThis is a limited Aoi_1 dialogue test. It replaces only:\n- GG2Game\\CookedPC\\Startup_LOC_INT.upk\n- GG2Game\\Localization\\INT\\Aoi_1_ENG.int\n- GG2Game\\Localization\\INT\\Aoi_1.int\n\nThe original Steam files are not modified by this folder. Back up the originals before copying these files into a test game installation. Restore the backups to undo the test.\n\nThe font package is based on the PC-compatible font patch workflow, not the Switch CharTextures.tfc.\n"""
(outroot/"README.txt").write_text(readme, encoding="utf-8")
print(outroot)
for p in outroot.rglob('*'):
    if p.is_file(): print(p, p.stat().st_size)
