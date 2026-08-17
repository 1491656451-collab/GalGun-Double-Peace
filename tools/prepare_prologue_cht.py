from pathlib import Path
import re, shutil
src = Path(r"D:\GALGUNVV\steam\GG2Game\Localization\INT\Common_Prologue_ENG.int")
text = src.read_text(encoding="utf-16")
# Small Traditional-Chinese conversion table for the opening-prologue test.
pairs = {
"时":"時","级":"級","樱":"櫻","这":"這","传":"傳","着":"著","个":"個","说":"說","虽":"雖","实":"實","欢":"歡","迎":"迎","学":"學","校":"校","请":"請","假":"假","听":"聽","长":"長","突":"突","为":"為","全":"全","过":"過","众":"眾","对":"對","表":"表","达":"達","只":"只","现":"現","气":"氣","场":"場","变":"變","级":"級","还":"還","见":"見","天":"天","使":"使","受":"受","传":"傳","响":"響","现":"現","盛":"盛","说":"說","法":"法","如":"如","今":"今","谈":"談","恋":"戀","爱":"愛","那":"那","位":"位","学":"學","生":"生","突":"突","然":"然","女":"女","人":"人","万":"萬","迷":"迷","面":"面","告":"告","白":"白","却":"卻","自":"自","己":"己","一":"一","唯":"唯","最":"最","后":"後","和":"和","她":"她","两":"兩","情":"情","相":"相","悦":"悅","离":"離","奇":"奇","更":"更","传":"傳","看":"看","升":"升","空":"空","受":"受","影":"影","响":"響","只":"只","会":"會","变":"變","得":"得","人":"人","爆":"爆","棚":"棚","或":"或","能":"能","心":"心","仪":"儀","对":"對","象":"象","流":"流","行":"行","不":"不","了":"了","倒":"倒","是":"是","完":"完","全":"全","没":"沒","谁":"誰","在":"在","那":"那","个":"個","叫":"叫","军":"軍","事":"事","感":"感","兴":"興","趣":"趣","吗":"嗎","等等":"等等","你":"你","是":"是","我":"我","的":"的","天":"天","津":"津","帕":"帕","塔":"塔","子":"子","年":"年","申":"申","请":"請","成":"成","立":"立","新":"新","研":"研","究":"究","所":"所","从":"從","早":"早","发":"發","放":"放","招":"招","募":"募","部":"部","员":"員","传":"傳","单":"單","对":"對","嗯":"嗯","太":"太","失":"失","落":"落","抱":"抱","歉":"歉","虽":"雖","然":"然","没":"沒","办":"辦","但":"但","如":"如","介":"介","意":"意","帮":"幫","后":"後","辈":"輩","下":"下","手":"手","真":"真","羞":"羞","忍":"忍","早":"早","好":"好","妹":"妹","昨":"昨","回":"回","来":"來","欸":"欸","久":"久","见":"見","酱":"醬","长":"長","高":"高","呢":"呢"
}
# Only patch the opening scene's first 30 dialogue entries.
lines = text.splitlines(keepends=True)
patched = 0
for i, line in enumerate(lines):
    if re.match(r'^Texts\[(?:[0-9]|[12][0-9])\]=', line):
        lines[i] = ''.join(pairs.get(ch, ch) for ch in line)
        patched += 1
patched_text = ''.join(lines)
# Include all chars actually used by the patched prologue in the font test.
chars = ''.join(sorted({ch for ch in patched_text if '\u3000' <= ch <= '\u9fff'}))
Path(r"D:\GALGUNVV\work\prologue_cht_chars.txt").write_text(chars, encoding="utf-8")
outroot = Path(r"D:\GALGUNVV\test_patch_cht_prologue")
loc = outroot / "GG2Game" / "Localization" / "INT"
loc.mkdir(parents=True, exist_ok=True)
for name in ("Common_Prologue.int", "Common_Prologue_ENG.int"):
    (loc / name).write_text(patched_text, encoding="utf-16")
print(f"patched_text_entries={patched} chars={len(chars)}")
