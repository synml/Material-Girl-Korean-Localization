"""Apply review fix files to translated_ko with safety checks.

Fix file format (review/fixes_*.txt):
    @@<file>#<idx>
    BEFORE: <exact current line>
    AFTER: <replacement line>
    WHY: <reason>

Safety: BEFORE must exactly match the line at idx (or idx±1 to absorb
off-by-one from 1-based viewers); engine lines (@/;;/*) are untouchable;
speaker voice ids must survive the edit.

Usage: uv run python tools/apply_review.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "translated_ko"
REVIEW = ROOT / "review"

HEAD_RE = re.compile(r"^@@([^#]+)#(\d+)\s*$")
VOICE_RE = re.compile(r"^\s*\[[^\]/]+/([^\]]+)\]")


def parse_fixes():
    fixes = []
    for path in sorted(REVIEW.glob("fixes_*.txt")):
        cur = None
        for line in path.read_text(encoding="utf-8").splitlines():
            m = HEAD_RE.match(line)
            if m:
                cur = {"file": m.group(1), "idx": int(m.group(2)), "src": path.name}
                fixes.append(cur)
            elif cur is not None:
                if line.startswith("BEFORE: "):
                    cur["before"] = line[8:]
                elif line.startswith("AFTER: "):
                    cur["after"] = line[7:]
                elif line.startswith("WHY: "):
                    cur["why"] = line[5:]
    return fixes


def main() -> None:
    fixes = parse_fixes()
    applied, skipped = [], []
    by_file = {}
    for fx in fixes:
        by_file.setdefault(fx["file"], []).append(fx)

    for fname, flist in by_file.items():
        p = SRC / fname
        if not p.exists():
            for fx in flist:
                skipped.append((fx, "file not found"))
            continue
        lines = p.read_text(encoding="utf-8", newline="").split("\n")
        changed = False
        for fx in flist:
            if "before" not in fx or "after" not in fx:
                skipped.append((fx, "malformed entry"))
                continue
            before, after = fx["before"], fx["after"]
            idx = None
            for cand in (fx["idx"], fx["idx"] - 1, fx["idx"] + 1):
                if 0 <= cand < len(lines) and lines[cand] == before:
                    idx = cand
                    break
            if idx is None:
                skipped.append((fx, "BEFORE does not match"))
                continue
            s = before.strip()
            if not s or s.startswith("@") or s.startswith(";;") or s.startswith("*"):
                skipped.append((fx, "engine/comment line untouchable"))
                continue
            vb = VOICE_RE.match(before)
            va = VOICE_RE.match(after)
            if vb and (not va or va.group(1) != vb.group(1)):
                skipped.append((fx, "voice id lost/changed"))
                continue
            if "\n" in after:
                skipped.append((fx, "AFTER not single line"))
                continue
            lines[idx] = after
            changed = True
            applied.append(fx)
        if changed:
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write("\n".join(lines))

    report = [f"applied: {len(applied)}, skipped: {len(skipped)}", ""]
    for fx, why in skipped:
        report.append(f"SKIP {fx['src']} {fx['file']}#{fx['idx']}: {why}")
    report.append("")
    for fx in applied:
        report.append(f"OK {fx['file']}#{fx['idx']}: {fx.get('why','')[:80]}")
    (REVIEW / "apply_report.txt").write_text("\n".join(report), encoding="utf-8")
    print(report[0])
    print("full report: review/apply_report.txt")


if __name__ == "__main__":
    main()
