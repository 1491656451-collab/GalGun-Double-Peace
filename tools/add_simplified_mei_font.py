from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import repack_font_uniform_cht as base


base.CURRENT_FONT_SIZE = 64951
base.OUT_DIR = Path(r"D:\GALGUNVV\work\font_add_9709")
base.OUT_PACKAGE = base.OUT_DIR / "Startup_LOC_INT.add_9709.upk"
base.REPORT = base.OUT_DIR / "font_add_9709_report.json"

original_target_codes = base.target_codes


def target_codes_with_mei() -> set[int]:
    codes = original_target_codes()
    codes.add(0x9709)
    codes.add(0x6963)
    return codes


base.target_codes = target_codes_with_mei


if __name__ == "__main__":
    base.main()
