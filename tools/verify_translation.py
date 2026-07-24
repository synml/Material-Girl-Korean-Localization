"""Structural verification of translated_ko against source_en.

Checks per file:
  - identical line count
  - non-translatable lines (@commands, ;; comments, *labels, blanks) byte-identical
  - voice ids preserved in speaker tags
  - \\C[n] / \\V[n] control-code multisets preserved (warning)
  - translatable lines actually translated (contains Hangul unless source had
    no latin letters) (warning)

Usage: uv run python tools/verify_translation.py
"""

import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source_en"
DST = ROOT / "translated_ko"

CODE_RE = re.compile(r"\\[A-Za-z]+\[[^\]]*\]|\\[.{}$|^!><]")
TAG_RE = re.compile(r"^\s*\[([^\]/]+?)(?:/([^\]]+?))?\]")
HANGUL_RE = re.compile(r"[가-힣]")
LATIN_RE = re.compile(r"[A-Za-z]")

# Narration point of view. The source narrates some files in 1st person and
# others in 3rd (SAKURA / 小櫻) — follow the source per line instead of
# normalising, so flag only KO 1st person against an unambiguously 3rd-person EN.
KO_FIRST_RE = re.compile(
    # "나와"는 동사 활용("끌려 나와")과 겹치므로 비교 구문에서만 잡는다
    r"(?:^|[\s（(“‘「『…—―,、])(나(?:는|도|의|를|랑|에게|한테|보다|까지|조차|뿐|만|같은)"
    r"|나와\s(?:달리|함께|같이)|내(?:가|\s|게|,)|우리(?:는|가|의|를|도)?)")
EN_FIRST_RE = re.compile(r"\b(I|I'?m|my|me|mine|we|our|us)\b", re.I)
EN_THIRD_RE = re.compile(r"\bSAKURA\b")


# Deliberate deviations from source_en (CH/dev-intent based repairs) — see CLAUDE.md §5-2.
# (file, 0-based idx) -> reason
WAIVERS = {
    ("A-saimin2-1b.txt", 9): "MT가 훼손한 @wait 명령 복원 (CH 기준)",
    ("A-sero07.txt", 18): "@select 선택지 한국어화",
    ("rp03.txt", 2): "@select 처녀/비처녀 루트 한국어화",
    ("rp04.txt", 3): "@select 처녀/비처녀 루트 한국어화",
    ("rp07.txt", 3): "@select 처녀/비처녀 루트 한국어화",
    ("rp10.txt", 3): "@select 처녀/비처녀 루트 한국어화",
    ("rp11_3a.txt", 3): "@select 처녀/비처녀 루트 한국어화",
    ("rp13_3a.txt", 3): "@select 처녀/비처녀 루트 한국어화",
    ("rp14.txt", 4): "@select 처녀/비처녀 루트 한국어화",
    ("rp16_1a.txt", 3): "@select 처녀/비처녀 루트 한국어화",
    ("rp18_1a.txt", 3): "@select 처녀/비처녀 루트 한국어화",
    ("rp18_2a.txt", 3): "@select 처녀/비처녀 루트 한국어화",
    ("rp18_3a.txt", 3): "@select 처녀/비처녀 루트 한국어화",
    ("rp20_1a.txt", 3): "@select 처녀/비처녀 루트 한국어화",
    ("rp20_2a.txt", 3): "@select 처녀/비처녀 루트 한국어화",
    ("rp20_3a.txt", 3): "@select 처녀/비처녀 루트 한국어화",
    ("rp02_1a.txt", 168): "@select 선택지 한국어화 (Definitely No! → 절대 싫어!, CH 기준)",
    ("rp08_2.txt", 120): "@se 명령 끝 잘못 붙은 ;; 제거 (CH 기준)",
    ("rp08_2.txt", 152): "@명령 선행 공백 제거 (CH 기준)",
    ("rp08_2.txt", 170): "@명령 선행 공백 제거 (CH 기준)",
    ("rp08_2.txt", 184): ";;주석 선행 공백 제거 (CH 기준)",
    ("rp08_2.txt", 296): ";;주석 선행 공백 제거 (CH 기준)",
    ("rp08_2.txt", 297): "@명령 선행 공백 제거 (CH 기준)",
    ("rp11_1a.txt", 1): ";;주석 선행 공백 제거 (CH 기준)",
    ("rp03.txt", 290): "EN 중복 보이스 ID skr0506→skr0507 (CH 기준, 파일 실존 확인)",
    ("rp10.txt", 140): "EN 오류 보이스 ID skr0955→skr0996 (CH 기준, 파일 실존 확인)",
    ("rp10.txt", 162): "EN 중복 보이스 ID skr1000→skr1001 (CH 기준, 파일 실존 확인)",
    ("rp20_4a.txt", 220): "EN이 텍스트로 치환한 @se 명령 복원 (CH 기준)",
    ("rp12_2b.txt", 19): "EN 중복 보이스 ID skr1249→skr1250 (CH 기준, 파일 실존 확인)",
    ("rp14.txt", 269): "EN 오류 보이스 ID skr1488→skr1448 (CH·전후 순번 기준, 파일 실존 확인)",
    ("rp13_3a.txt", 245): "EN에 노출된 개발 메모 주석화 (CH 기준)",
}


def is_fixed(line: str) -> bool:
    s = line.strip()
    return (not s) or s.startswith("@") or s.startswith(";;") or s.startswith("*")


errors = []
warnings = []
files = 0

for src in sorted(SRC.glob("*.txt")):
    dst = DST / src.name
    if not dst.exists():
        errors.append(f"{src.name}: MISSING output file")
        continue
    files += 1
    a = src.read_text(encoding="utf-8", newline="").split("\n")
    b = dst.read_text(encoding="utf-8", newline="").split("\n")
    if len(a) != len(b):
        errors.append(f"{src.name}: line count {len(a)} -> {len(b)}")
        continue
    for i, (la, lb) in enumerate(zip(a, b)):
        if (src.name, i) in WAIVERS:
            continue
        if is_fixed(la):
            if la != lb:
                errors.append(f"{src.name}#{i}: fixed line changed")
            continue
        ma, mb = TAG_RE.match(la), TAG_RE.match(lb)
        if ma:
            if not mb:
                errors.append(f"{src.name}#{i}: speaker tag lost")
            elif (ma.group(2) or "").strip() != (mb.group(2) or "").strip():
                errors.append(f"{src.name}#{i}: voice id changed {ma.group(2)} -> {mb.group(2)}")
        ca, cb = Counter(CODE_RE.findall(la)), Counter(CODE_RE.findall(lb))
        if ca != cb:
            warnings.append(f"{src.name}#{i}: control codes {dict(ca)} -> {dict(cb)}")
        if len(LATIN_RE.findall(la)) >= 4 and not HANGUL_RE.search(lb):
            warnings.append(f"{src.name}#{i}: no Hangul in translation")
        # narration only: no speaker tag, not a （…） monologue, not a \CL system line
        sb = lb.strip()
        if sb and sb[0] not in "[（(" and not sb.startswith("\\CL"):
            if KO_FIRST_RE.search(sb) and EN_THIRD_RE.search(la) and not EN_FIRST_RE.search(la):
                warnings.append(f"{src.name}#{i}: 지문 1인칭 / 원문 3인칭")

print(f"checked {files} files: {len(errors)} errors, {len(warnings)} warnings")
report = ["== ERRORS =="] + errors + ["", "== WARNINGS =="] + warnings
out = ROOT / "review" / "verify_report.txt"
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(report), encoding="utf-8")
print("full report: review/verify_report.txt")
