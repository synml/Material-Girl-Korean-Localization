"""Rebuild Korean scenario text files from translated units.

Reads:
  work/units.jsonl                - extraction metadata
  work/translated/batch_*.txt     - agent outputs: `@@file#idx` sentinel line
                                    followed by exactly one Korean line
  tools/name_map.json             - raw speaker tag -> Korean display name

Writes:
  translated_ko/*.txt             - full Korean scenario files
  work/inject_report.txt          - coverage / problem report

Usage: uv run python tools/inject_units.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
SRC_EN = ROOT / "source_en"
OUT = ROOT / "translated_ko"

SENT_RE = re.compile(r"^@@([^#]+)#(\d+)\s*$")


def load_units():
    units = {}
    with open(WORK / "units.jsonl", encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            units[(u["file"], u["idx"])] = u
    return units


def load_translations():
    trans = {}
    problems = []
    for tf in sorted((WORK / "translated").glob("batch_*.txt")):
        cur_key = None
        buf = []
        def flush():
            nonlocal cur_key, buf
            if cur_key is not None:
                text = " ".join(s for s in (b.strip() for b in buf) if s)
                if text.startswith("KO:"):
                    text = text[3:].strip()
                if not text:
                    problems.append(f"{tf.name}: empty translation for {cur_key}")
                else:
                    if len(buf) > 1:
                        problems.append(f"{tf.name}: multi-line joined for {cur_key}")
                    if cur_key in trans and trans[cur_key] != text:
                        problems.append(f"{tf.name}: duplicate differing translation for {cur_key}")
                    trans[cur_key] = text
            cur_key, buf = None, []
        for line in tf.read_text(encoding="utf-8").splitlines():
            m = SENT_RE.match(line)
            if m:
                flush()
                cur_key = (m.group(1), int(m.group(2)))
            elif cur_key is not None:
                if line.startswith("### FILE"):
                    flush()
                else:
                    buf.append(line)
        flush()
    return trans, problems


def main() -> None:
    units = load_units()
    name_map = json.loads((ROOT / "tools" / "name_map.json").read_text(encoding="utf-8"))
    trans, problems = load_translations()
    OUT.mkdir(exist_ok=True)

    missing = []
    unknown = [k for k in trans if k not in units]
    unknown_tags = set()

    by_file = {}
    for (fname, idx), u in units.items():
        by_file.setdefault(fname, {})[idx] = u

    written = 0
    for f in sorted(SRC_EN.glob("*.txt")):
        lines = f.read_text(encoding="utf-8", newline="").split("\n")
        file_units = by_file.get(f.name, {})
        complete = True
        for idx, u in file_units.items():
            key = (f.name, idx)
            if key not in trans:
                missing.append(f"{f.name}#{idx}")
                complete = False
                continue
            body = trans[key]
            if u["tag"] is not None:
                ko_name = name_map.get(u["tag"])
                if ko_name is None:
                    ko_name = name_map.get(u["tag"].strip())
                if ko_name is None:
                    unknown_tags.add(u["tag"])
                    ko_name = u["tag"]
                tag = f"[{ko_name}/{u['voice']}]" if u["voice"] else f"[{ko_name}]"
                lines[idx] = u["prefix"] + tag + body
            else:
                lines[idx] = u["prefix"] + body
        with open(OUT / f.name, "w", encoding="utf-8", newline="") as out:
            out.write("\n".join(lines))
        written += 1 if complete else 0

    report = [
        f"translations loaded: {len(trans)}",
        f"units total: {len(units)}",
        f"missing translations: {len(missing)}",
        f"unknown sentinels: {len(unknown)}",
        f"unknown speaker tags: {sorted(unknown_tags)}",
        f"files fully covered: {written}/{len(list(SRC_EN.glob('*.txt')))}",
        "",
        "-- problems --",
        *problems[:200],
        "",
        "-- missing --",
        *missing[:400],
        "",
        "-- unknown sentinel keys --",
        *[f"{k[0]}#{k[1]}" for k in unknown[:100]],
    ]
    (WORK / "inject_report.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report[:8]))
    print("full report: work/inject_report.txt")


if __name__ == "__main__":
    main()
