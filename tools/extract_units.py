"""Extract translatable lines from decoded scenario files into work units.

Produces:
  work/units.jsonl            - one JSON object per translatable line
  work/tasks/batch_NNN.txt    - agent-facing task files (EN + CH context)
  work/batches.json           - batch -> files mapping

A line is translatable unless it is empty, an @engine command, a ;; comment,
or a *label. Speaker tags [NAME/voice] are split off; agents translate only
the body text. CH text is paired line-by-line inside runs of consecutive
translatable lines between structural anchors; if a run's lengths differ,
the whole CH run is attached as block context.

Usage: uv run python tools/extract_units.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_EN = ROOT / "source_en"
SRC_CH = ROOT / "source_ch"
WORK = ROOT / "work"
TASKS = WORK / "tasks"

TAG_RE = re.compile(r"^(\s*)\[([^\]/]+?)(?:/([^\]]+?))?\](.*)$")
BATCH_CHAR_TARGET = 16000  # EN chars per batch, split at file boundaries


def is_translatable(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.startswith("@") or s.startswith(";;") or s.startswith("*"):
        return False
    return True


def runs_of_text(lines: list[str]):
    """Yield (start_idx, [line, ...]) runs of consecutive translatable lines."""
    run = []
    start = None
    for i, line in enumerate(lines):
        if is_translatable(line):
            if start is None:
                start = i
            run.append(line)
        else:
            if run:
                yield start, run
            run, start = [], None
    if run:
        yield start, run


def parse_line(line: str):
    m = TAG_RE.match(line)
    if m:
        prefix, name, voice, body = m.groups()
        return {"prefix": prefix, "tag": name, "voice": voice, "body": body}
    m2 = re.match(r"^(\s*)(.*)$", line)
    return {"prefix": m2.group(1), "tag": None, "voice": None, "body": m2.group(2)}


def strip_tag(line: str) -> str:
    m = TAG_RE.match(line)
    return m.group(4).strip() if m else line.strip()


def main() -> None:
    TASKS.mkdir(parents=True, exist_ok=True)
    files = sorted(SRC_EN.glob("*.txt"), key=lambda p: p.name)

    all_units = []
    per_file_units = {}

    for f in files:
        en_lines = f.read_text(encoding="utf-8").splitlines()
        ch_path = SRC_CH / f.name
        ch_lines = ch_path.read_text(encoding="utf-8").splitlines() if ch_path.exists() else []

        en_runs = list(runs_of_text(en_lines))
        ch_runs = [run for _, run in runs_of_text(ch_lines)]

        units = []
        for run_no, (start, run) in enumerate(en_runs):
            ch_run = ch_runs[run_no] if run_no < len(ch_runs) else []
            aligned = len(ch_run) == len(run)
            ch_block = None if aligned else " / ".join(strip_tag(c) for c in ch_run) or None
            for k, line in enumerate(run):
                p = parse_line(line)
                ch_text = strip_tag(ch_run[k]) if aligned and k < len(ch_run) else ch_block
                units.append({
                    "file": f.name,
                    "idx": start + k,
                    "prefix": p["prefix"],
                    "tag": p["tag"],
                    "voice": p["voice"],
                    "en": p["body"],
                    "ch": ch_text,
                    "ch_aligned": aligned,
                })
        per_file_units[f.name] = units
        all_units.extend(units)

    with open(WORK / "units.jsonl", "w", encoding="utf-8") as out:
        for u in all_units:
            out.write(json.dumps(u, ensure_ascii=False) + "\n")

    # --- batching ---
    batches = []
    cur, cur_chars = [], 0
    for f in files:
        units = per_file_units[f.name]
        chars = sum(len(u["en"]) for u in units)
        if not units:
            continue
        if cur and cur_chars + chars > BATCH_CHAR_TARGET:
            batches.append(cur)
            cur, cur_chars = [], 0
        cur.append(f.name)
        cur_chars += chars
    if cur:
        batches.append(cur)

    batch_map = {}
    for bi, fnames in enumerate(batches, 1):
        bname = f"batch_{bi:03d}"
        batch_map[bname] = fnames
        with open(TASKS / f"{bname}.txt", "w", encoding="utf-8") as out:
            for fname in fnames:
                out.write(f"### FILE: {fname}\n")
                for u in per_file_units[fname]:
                    speaker = u["tag"] if u["tag"] else "narration"
                    out.write(f"@@{fname}#{u['idx']} [{speaker}]\n")
                    out.write(f"EN: {u['en'].strip()}\n")
                    if u["ch"]:
                        marker = "CH" if u["ch_aligned"] else "CH-block"
                        out.write(f"{marker}: {u['ch']}\n")
                out.write("\n")

    with open(WORK / "batches.json", "w", encoding="utf-8") as out:
        json.dump(batch_map, out, ensure_ascii=False, indent=1)

    total_chars = sum(len(u["en"]) for u in all_units)
    print(f"files: {len(files)}, units: {len(all_units)}, EN chars: {total_chars}, batches: {len(batches)}")


if __name__ == "__main__":
    main()
