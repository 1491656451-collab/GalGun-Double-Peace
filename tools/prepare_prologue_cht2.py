from pathlib import Path
import re
src = Path(r"D:\GALGUNVV\steam\GG2Game\Localization\INT\Common_Prologue_ENG.int")
text = src.read_text(encoding="utf-16")
pairs = str.maketrans({
"时":"時","级":"級","樱":"櫻","这":"這","传":"傳","着":"著","个":"個","说":"說","虽":"雖","实":"實","欢":"歡","学":"學","请":"請","听":"聽","长":"長","为":"為","后":"後","众":"眾","对":"對","达":"達","现":"現","气":"氣","场":"場","变":"變","还":"還","见":"見","欢":"歡","响":"響","万":"萬","恋":"戀","爱":"愛","两":"兩","悦":"悅","离":"離","谈":"談","仪":"儀","兴":"興","没":"沒","来":"來","发":"發","员":"員","从":"從","帮":"幫","辈":"輩","单":"單","军":"軍","种":"種","话":"話","亲":"親","称":"稱","里":"裡","们":"們","麼":"麼","儀":"儀"
})
lines=text.splitlines(keepends=True)
for i,line in enumerate(lines):
    if re.match(r'^Texts\[(?:[0-9]|[12][0-9])\]=',line):
        line=line.translate(pairs)
        for a,b in {
            "人稱":"人稱","已經夠":"已經夠","傳聞":"傳聞","親眼":"親眼","裡盛傳":"裡盛傳","這種說法":"這種說法","不過話說回來":"不過話說回來","這所學校":"這所學校","去了":"去了"
        }.items(): line=line.replace(a,b)
        lines[i]=line
patched=''.join(lines)
chars=''.join(sorted({ch for ch in patched if '\u3000'<=ch<='\u9fff'}))
Path(r"D:\GALGUNVV\work\prologue_cht_chars.txt").write_text(chars,encoding='utf-8')
out=Path(r"D:\GALGUNVV\test_patch_cht_prologue\GG2Game\Localization\INT")
for n in ('Common_Prologue.int','Common_Prologue_ENG.int'):(out/n).write_text(patched,encoding='utf-16')
print('chars',len(chars))


