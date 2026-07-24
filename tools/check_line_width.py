# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools"]
# ///
"""Display-width check: does any text row overflow the message window?

RPG Maker MV never wraps text by itself. This game wraps inside
TS_ADVsystem.viewMesAdjust() by counting *characters* (halfwidth and fullwidth
alike), and the stock plugin doubles that budget for the English slot because
Latin glyphs are narrow. Korean glyphs are not, so the English budget lets a row
run past the window and the right end is clipped. patch/www/js/plugins/
TS_ADVsystem.js therefore overrides the budget; this script re-implements the
same wrap and measures every produced row with the real font metrics, so the
override and the text stay verifiably in sync.

Covers every path that can put text in a window:
  - translated_ko/*.txt        scenario  (wrapped: viewMesAdjust)
  - patch_data/map_text_ko     Show Text (wrapped: command401 -> viewMesAdjust)
  - patch_data/choices_ko      choices   (NOT wrapped)
  - patch_data/event_ui_ko     choices   (NOT wrapped)
  - patch_data/db_en_ko        name / nickname / profile / description (NOT wrapped)

Usage: uv run tools/check_line_width.py [game_dir]
       (note: no "python" — the inline dependency block above needs uv's
        script runner to install fontTools)
"""

import json
import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GAME = Path(r"D:\SteamLibrary\steamapps\common\Material Girl")

# Window_Base.standardFontSize / standardPadding (www/js/rpg_windows.js);
# boxWidth comes from YEP_CoreEngine's "Screen Width" parameter.
BOX_WIDTH = 1024
PADDING = 18
FONT_SIZE = 28
DRAW_W = BOX_WIDTH - PADDING * 2          # 988px of drawable content
LIMIT = DRAW_W - 24                       # keep a glyph of slack

# viewMesAdjust internals (TS_ADVsystem.js)
SPACE_AJASUTO = "　" * 4
F_SPACE = "　" + SPACE_AJASUTO
SPACE = F_SPACE + "　"
SPACE_ONE = SPACE + "　"
FOLLOWING = ("%),:;]}｡｣ﾞﾟ。，、．：；゛゜ヽヾゝ"
             "ゞ々’”）〕］｝〉》」』】°′″℃￠％‰　 ")
ESCAPE = re.compile(r'^[\$\.\|\^!><\{\}\[\]\\]|^[A-Z]|^\d')
# Codes consumed before drawing (Window_Base.convertEscapeCharacters / obtainEscapeCode)
CTRL = re.compile(r'\\(?:C\[\d+\]|V\[\d+\]|N\[\d+\]|P\[\d+\]|CL|[GIS$.!|^><])', re.I)


def wrap_style() -> tuple[int, str, str, str]:
    """Read the Korean row budget and indents straight out of the patched plugin,
    so this checker can never disagree with what the game actually runs."""
    js = (ROOT / "patch/www/js/plugins/TS_ADVsystem.js").read_text(encoding="utf-8")
    m = re.search(r'langSelect == 1\)\{.*?view_text_num\s*=\s*(\d+)\s*;', js, re.S)
    if not m:
        sys.exit("error: could not read the Korean wrap budget from the patched "
                 "TS_ADVsystem.js — did the override get lost?")
    budget = int(m.group(1))

    def indent(var: str, default: str) -> str:
        mo = re.search(r'langSelect == 1\)\{.*?\b' + var + r'\s*=\s*"([^"]*)"', js, re.S)
        return mo.group(1) if mo else default

    return (budget,
            indent("text_f_space", F_SPACE),
            indent("text_space", SPACE),
            indent("text_space_one", SPACE_ONE))


def name_voice_cut(text: str) -> str:
    """ADV_System.nameVoiceCut: drop the /voiceID part of a speaker tag."""
    if "/" in text and "[" in text and "]" in text:
        head = text.split("]")[0]
        return text.replace(head, head.split("/")[0], 1)
    return text


def view_mes_adjust(text: str, budget: int, spaces: tuple[str, str, str]) -> str:
    """Port of ADV_System.viewMesAdjust (character-counted wrap + indent)."""
    output = ""
    text_f_space, text_space, text_space_one = spaces
    if re.search("CL", text, re.I):        # NO_SPACE = /\CL/i -> literal "CL"
        text_space = text_f_space = text_space_one = ""

    cnt, text_len, voice = 0, 0, False
    if text.startswith("["):               # speaker line: name gets its own row
        text = text_f_space + text
        text = text.replace("]", "]\n" + text_f_space, 1)
        text_len = len(text.split("]\n")[0]) + 1
        voice = True
        if "]\n" in text:
            text = text.replace("]", "", 1)
            text = text.replace("[", "", 1)
            text_len -= 2
    else:                                  # narration: leading blank row + indent
        output = "\n" + text_space_one
        cnt = len(text_space)

    escape_text = False
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\":
            escape_text = True
        if escape_text:
            escape_text = ESCAPE.match(c) is not None
        if voice and text_len < cnt:
            voice = False
            cnt = 0
        if not voice and cnt >= budget:
            if c in FOLLOWING:             # no line-leading punctuation
                output += c
            else:
                output += "\n" + text_space + c
                cnt = len(text_space)
        elif c == "\\" and i + 1 < len(text) and text[i + 1] == "n":
            output += "\n" + text_space
            cnt = len(text_space)
            i += 1
        else:
            output += c
        if not escape_text:
            cnt += 1
        i += 1
    return output


class Metrics:
    """Advance widths: bundled Pretendard first, then the game's M+ fallback."""

    def __init__(self, game: Path) -> None:
        paths = [ROOT / "patch/www/fonts/Pretendard-Regular.otf",
                 game / "www/fonts/mplus-1m-regular.ttf"]
        self.fonts = []
        for p in paths:
            if p.exists():
                f = TTFont(str(p), lazy=True)
                self.fonts.append((f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm))
        if not self.fonts:
            sys.exit(f"error: no font found (looked for {paths[0]})")
        self.cache: dict[tuple[str, int], float] = {}

    def char_w(self, ch: str, size: int) -> float:
        key = (ch, size)
        if key not in self.cache:
            w = float(size)                # unmapped: assume fullwidth
            for cmap, hmtx, upem in self.fonts:
                g = cmap.get(ord(ch))
                if g:
                    w = hmtx[g][0] / upem * size
                    break
            self.cache[key] = w
        return self.cache[key]

    def row_w(self, row: str) -> float:
        row = CTRL.sub("", row)
        size, w, i = FONT_SIZE, 0.0, 0
        while i < len(row):
            if row[i] == "\\" and i + 1 < len(row) and row[i + 1] in "{}":
                size += 12 if row[i + 1] == "{" else -12   # makeFontBigger/Smaller
                i += 2
                continue
            w += self.char_w(row[i], size)
            i += 1
        return w


def check_wrapped(text: str, where: str, wrap, m: Metrics, bad: list) -> None:
    for row in view_mes_adjust(name_voice_cut(text), wrap[0], wrap[1:]).split("\n"):
        w = m.row_w(row)
        if w > LIMIT:
            bad.append((w, where, row.strip()))


def check_plain(text: str, where: str, m: Metrics, bad: list) -> None:
    for row in text.split("\n"):
        w = m.row_w(row)
        if w > LIMIT:
            bad.append((w, where, row.strip()))


def main() -> None:
    game = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_GAME
    m = Metrics(game)
    wrap = wrap_style()
    bad: list[tuple[float, str, str]] = []

    n_rows = 0
    for f in sorted((ROOT / "translated_ko").glob("*.txt")):
        for ln, raw in enumerate(f.read_text(encoding="utf-8", newline="").split("\n"), 1):
            t = raw.replace("\r", "").strip()
            if not t or t[0] in "@*;":
                continue
            n_rows += 1
            check_wrapped(t, f"{f.name}:{ln}", wrap, m, bad)

    mt = json.loads((ROOT / "patch_data/map_text_ko.json").read_text(encoding="utf-8"))
    for ja, ko in mt.items():
        check_wrapped(ko, f"map_text_ko[{ja[:20]}…]", wrap, m, bad)

    ui = json.loads((ROOT / "patch_data/map_ui_ko.json").read_text(encoding="utf-8"))
    for src, ko in ui.items():
        if src.startswith("_"):
            continue
        # Short entries are choice labels (Window_ChoiceList, no wrap); the long
        # ones are Show Text and go through viewMesAdjust like scenario lines.
        if len(ko) < 40:
            check_plain(ko, f"map_ui_ko[{src[:20]}…]", m, bad)
        else:
            check_wrapped(ko, f"map_ui_ko[{src[:20]}…]", wrap, m, bad)

    cond = re.compile(r'^(?:if|en|sw|dis|hide|ext)\s*\([^)]*\)')   # MPP_ChoiceEX prefix
    for table in ("choices_ko", "event_ui_ko"):
        ch = json.loads((ROOT / f"patch_data/{table}.json").read_text(encoding="utf-8"))
        for key, ko in ch.items():
            if key.startswith("_"):
                continue
            check_plain(cond.sub("", ko), f"{table}[{key[:20]}…]", m, bad)

    db = json.loads((ROOT / "patch_data/db_en_ko.json").read_text(encoding="utf-8"))
    for key, ko in db.items():
        # <en:> is comma-split by RTK1_Option_EnJa: actors take name,nickname,
        # profile; everything else takes name,description.
        for field in ko.split(",")[1:]:
            check_plain(field, f"db_en_ko[{key}]", m, bad)

    print(f"scenario lines checked: {n_rows}   wrap budget: {wrap[0]} chars, "
          f"indent {len(wrap[1])}/{len(wrap[2])}/{len(wrap[3])} (langSelect==1)   "
          f"limit: {LIMIT:.0f}px of {DRAW_W}px")
    if not bad:
        print("no overflowing rows")
        return
    print(f"{len(bad)} overflowing rows:")
    for w, where, row in sorted(bad, reverse=True):
        print(f"  {w:7.0f}px  {where}  {row[:60]}")
    sys.exit(1)


if __name__ == "__main__":
    main()
