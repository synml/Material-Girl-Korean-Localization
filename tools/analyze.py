"""Analyze decoded scenario files: speakers, @commands, volume stats.

Usage: uv run python tools/analyze.py source_en
"""

import re
import sys
from collections import Counter
from pathlib import Path

src = Path(sys.argv[1])
files = sorted(src.glob("*.txt"))

speakers = Counter()
commands = Counter()
total_chars = 0
total_lines = 0
dialogue_lines = 0

tag_re = re.compile(r"^\[([^/\]]+)(?:/([^\]]+))?\]")

for f in files:
    for line in f.read_text(encoding="utf-8").splitlines():
        total_lines += 1
        s = line.strip()
        if not s:
            continue
        if s.startswith("@"):
            commands[s.split()[0]] += 1
            continue
        if s.startswith(";;"):
            continue
        total_chars += len(s)
        dialogue_lines += 1
        m = tag_re.match(s)
        if m:
            speakers[m.group(1)] += 1

print(f"files: {len(files)}, lines: {total_lines}, text lines: {dialogue_lines}, text chars: {total_chars}")
print("\n== speakers ==")
for name, n in speakers.most_common():
    print(f"{n:6d}  {name}")
print("\n== commands ==")
for cmd, n in commands.most_common():
    print(f"{n:6d}  {cmd}")
