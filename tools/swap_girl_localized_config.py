from pathlib import Path


CONFIG = Path(r"D:\SteamLibrary\steamapps\common\GalGun Double Peace\GG2Game\Config\GG2GG2GIrlDatas.ini")
OLD = "localizedData[0]=GG2GirlLocalizedData'GG2GIrlDatas_Eng.localizedData."
NEW = "localizedData[0]=GG2GirlLocalizedData'GG2GIrlDatas.localizedData."


def main() -> None:
    raw = CONFIG.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise RuntimeError("unexpected UTF-16 config; refusing to rewrite")
    text = raw.decode("utf-8")
    count = text.count(OLD)
    if count != 79:
        raise RuntimeError(f"expected 79 English localized references, found {count}")
    updated = text.replace(OLD, NEW)
    CONFIG.write_bytes(updated.encode("utf-8"))
    print(f"replaced={count}")


if __name__ == "__main__":
    main()
