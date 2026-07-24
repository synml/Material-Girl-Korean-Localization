"""Automated consistency scan over translated_ko.

Checks:
  - forbidden name/term variants (glossary drift)
  - residual Japanese kana / Han characters (ja/ch source left in place)
  - unexpected long Latin runs (allowlist-filtered)
  - unbalanced quotes/parens and \\C[2]..\\C[0] pairs per line
  - known Korean typo patterns

Usage: uv run python tools/review_scan.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "translated_ko"

# term -> reason (things that must NOT appear)
FORBIDDEN = {
    "시이": "SHI 잔재 - 츠카사로 통일",
    "곤도": "콘도 오표기",
    "콘도우": "콘도 오표기",
    "쿠로다": "구로다 오표기",
    "시로사와": "시라사와 오표기",
    "사다케": "사타케 오표기",
    "마카오카": "마키오카 오표기",
    "아사히꼬": "아사히코 오표기",
    "오파이": "가슴펍으로 통일",
    "오빠팟": "가슴펍으로 통일",
    "블루세라": "부르세라로 통일",
    "오컬트부": "초자연연구부로 통일",
    "오컬트 연구부": "초자연연구부로 통일",
    "음탕도": "음란도로 통일",
    "나카다시": "질내사정/안에 싸기로 통일",
    "육변소": "육변기로 통일",
    "미친 칼날": "광기의 칼날로 통일",
    "'": "반각 작은따옴표 — 전각 ‘ ’ 사용",
    "가터벨트": "팬티스타킹으로 통일 (게임 내부 아이템명 パンスト 기준)",
    "종군 카메라맨": "종군 기자로 통일",
    "됬": "맞춤법: 됐",
    "웬지 ": "맞춤법: 왠지",
    "왠일": "맞춤법: 웬일",
    "어떡게": "맞춤법: 어떻게",
    "오랫만": "맞춤법: 오랜만",
    "희안": "맞춤법: 희한",
    "들어난": "맞춤법: 드러난",
    "들어났": "맞춤법: 드러났",
    "바램": "맞춤법: 바람(소망)",
    "설레임": "맞춤법: 설렘",
    "역활": "맞춤법: 역할",
    "금새 ": "맞춤법: 금세",
    "요세": "맞춤법: 요새",
    "낳아지": "맞춤법: 나아지",
    "문안하": "맞춤법: 무난하",
    "쳐박": "맞춤법: 처박",
    # 번역투 (2차 검토에서 확인된 확정 오류형)
    "오야": "감탄사 음역 잔재(おや) — 어라/이런/이봐",
    "핥아지": "일본식 피동 직역 — 핥아주다 능동으로",
    "말을 걸린": "일본식 피동 직역 — 말을 걸어오다",
    "놀러 쓰": "비문 — 노는 데 쓰다",
    "절정에 도착": "연어 오류 — 절정에 도달",
    "근질거려진": "비문",
    "부비 일부": "部費 직역 — 동아리 예산",
    "부비에서": "部費 직역 — 동아리 예산",
    "지금 사이에": "직역투(今のうちに) — 지금 이 틈에",
}

# (regex, reason) — 항상 틀린 형태만 등록 (오탐 금지 원칙)
FORBIDDEN_RE = [
    (re.compile(r'(?<![\d,])\d{4,}\s*엔'), "금액 콤마 누락 — 1,000엔 형식"),
    (re.compile(r'"[^"]*"'), '반각 따옴표 — 전각 “ ” 사용'),
    # 구두점 폭은 반각으로 통일 (전체의 83~86%가 반각이었다)
    (re.compile(r'[！？]'), '전각 감탄·물음표 — 반각 ! ? 로 통일'),
    (re.compile(r'[가-힣]\.(?:」|』|）)'), '「…」 안 끝 마침표 — 생략으로 통일'),
]

KANA_RE = re.compile(r"[぀-ゟ゠-ヿ]")
# 한자는 한국어 본문에 쓰지 않는다 → 남아 있으면 일본어/중국어 원문 잔존이다
HAN_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
LATIN_RE = re.compile(r"[A-Za-z]{3,}")
LATIN_ALLOW = {
    "Beautiful", "GAME", "OVER", "END", "THE", "OK", "VR", "CG", "TV",
    "WASD", "No", "OH", "SEX", "Sex", "MAX", "DVD", "NG", "PC",
    "LINE", "VIP", "KFC", "BGM",  # 실존 고유명·통용 외래어 (CLAUDE.md §5-1)
}
PAIRS = [("「", "」"), ("『", "』"), ("（", "）")]


def is_fixed(line: str) -> bool:
    s = line.strip()
    return (not s) or s.startswith("@") or s.startswith(";;") or s.startswith("*")


issues = []
for f in sorted(SRC.glob("*.txt")):
    for i, line in enumerate(f.read_text(encoding="utf-8").split("\n")):
        if is_fixed(line):
            continue
        for term, why in FORBIDDEN.items():
            if term in line:
                issues.append(f"{f.name}#{i}\t[{why}]\t{line.strip()[:80]}")
        for rx, why in FORBIDDEN_RE:
            if rx.search(line):
                issues.append(f"{f.name}#{i}\t[{why}]\t{line.strip()[:80]}")
        if KANA_RE.search(line):
            issues.append(f"{f.name}#{i}\t[가나 잔존]\t{line.strip()[:80]}")
        if HAN_RE.search(line):
            issues.append(f"{f.name}#{i}\t[한자 잔존]\t{line.strip()[:80]}")
        for m in LATIN_RE.finditer(line):
            w = m.group(0)
            if w not in LATIN_ALLOW and not w.startswith(("skr", "rp", "ev", "cg")):
                issues.append(f"{f.name}#{i}\t[라틴 잔존:{w}]\t{line.strip()[:80]}")
        for a, b in PAIRS:
            if line.count(a) != line.count(b):
                issues.append(f"{f.name}#{i}\t[짝 불일치 {a}{b}]\t{line.strip()[:80]}")
        c_open = len(re.findall(r"\\C\[[1-9]\d*\]", line))
        c_close = len(re.findall(r"\\C\[0\]", line))
        if c_open != c_close:
            issues.append(f"{f.name}#{i}\t[색코드 짝: open{c_open}/close{c_close}]\t{line.strip()[:80]}")

out = ROOT / "review" / "scan_report.txt"
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(issues), encoding="utf-8")
print(f"{len(issues)} issues -> {out}")
