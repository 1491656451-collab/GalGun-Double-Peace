from pathlib import Path
p=Path(r"D:\GALGUNVV\test_patch_cht_prologue\GG2Game\Localization\INT\Common_Prologue_ENG.int")
text=p.read_text(encoding='utf-16')
for a,b in {'傳闻':'傳聞','闻':'聞','传闻':'傳聞','已经':'已經','够':'夠','亲':'親','里':'裡','种':'種','却':'卻','会':'會','说':'說','来':'來','长':'長','见':'見','听':'聽','学':'學','后':'後','个':'個','们':'們','两':'兩','为':'為','场':'場','气':'氣','变':'變','发':'發','欢':'歡','恋':'戀','爱':'愛','万':'萬','对':'對','众':'眾','实':'實','虽':'雖','时':'時','级':'級','请':'請'}.items(): text=text.replace(a,b)
for n in ('Common_Prologue.int','Common_Prologue_ENG.int'):
    Path(r"D:\GALGUNVV\test_patch_cht_prologue\GG2Game\Localization\INT" , n).write_text(text,encoding='utf-16')
chars=''.join(sorted({ch for ch in text if '\u3000'<=ch<='\u9fff'}))
Path(r"D:\GALGUNVV\work\prologue_cht_chars.txt").write_text(chars,encoding='utf-8')
print('chars',len(chars))
