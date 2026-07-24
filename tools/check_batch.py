"""Check one translated batch file for completeness before injection.

Usage: uv run python tools/check_batch.py batch_001 [batch_002 ...]
       uv run python tools/check_batch.py all
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
SENT_RE = re.compile(r"^@@([^#]+)#(\d+)\s*$")
HANGUL_RE = re.compile(r"[가-힣]")
LATIN4_RE = re.compile(r"[A-Za-z].*[A-Za-z].*[A-Za-z].*[A-Za-z]")

units = {}
with open(WORK / "units.jsonl", encoding="utf-8") as f:
    for line in f:
        u = json.loads(line)
        units.setdefault(u["file"], {})[u["idx"]] = u

batches = json.loads((WORK / "batches.json").read_text(encoding="utf-8"))

names = sys.argv[1:]
if names == ["all"]:
    names = sorted(batches.keys())

overall_fail = 0
for bname in names:
    path = WORK / "translated" / f"{bname}.txt"
    if not path.exists():
        print(f"{bname}: OUTPUT MISSING")
        overall_fail += 1
        continue
    expected = set()
    for fname in batches[bname]:
        for idx in units.get(fname, {}):
            expected.add((fname, idx))
    got = {}
    cur = None
    extra_junk = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        m = SENT_RE.match(line)
        if m:
            cur = (m.group(1), int(m.group(2)))
            got.setdefault(cur, [])
        elif line.strip():
            if cur is None:
                extra_junk += 1
            else:
                got[cur].append(line.strip())
    missing = expected - set(got)
    unknown = set(got) - expected
    empty = [k for k, v in got.items() if not v]
    multi = [k for k, v in got.items() if len(v) > 1]
    no_hangul = []
    for k, v in got.items():
        if k in expected and v:
            src = units[k[0]][k[1]]["en"]
            if LATIN4_RE.search(src) and not HANGUL_RE.search(" ".join(v)):
                no_hangul.append(k)
    status = "OK" if not (missing or unknown or empty or multi or extra_junk) else "FAIL"
    if status == "FAIL":
        overall_fail += 1
    print(f"{bname}: {status}  units {len(got)}/{len(expected)}"
          f"  missing={len(missing)} unknown={len(unknown)} empty={len(empty)}"
          f" multiline={len(multi)} junk={extra_junk} noHangul={len(no_hangul)}")
    for k in sorted(missing)[:10]:
        print(f"   missing {k[0]}#{k[1]}")
    for k in sorted(unknown)[:10]:
        print(f"   unknown {k[0]}#{k[1]}")
    for k in sorted(multi)[:10]:
        print(f"   multiline {k[0]}#{k[1]}")
    for k in sorted(no_hangul)[:10]:
        print(f"   noHangul {k[0]}#{k[1]}")

sys.exit(1 if overall_fail else 0)
