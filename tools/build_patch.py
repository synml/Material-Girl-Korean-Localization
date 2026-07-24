"""Assemble the final patch tree from translated resources.

Steps:
  1. translated_ko/*.txt  --XOR encode-->  patch/scenario/En/*.sl
  2. CommonEvents.json: replace the En slot of every "Ja ||| En ||| Ch" choice
     string using patch_data/choices_ko.json (keyed "ja|||ch", both stripped),
     then patch_data/event_ui_ko.json for the choices the devs branched on the
     language variable instead of packing into one "|||" string
  3. Database jsons: replace <en:...> note content using patch_data/db_en_ko.json
  4. System.json: rewrite the term arrays as "ja||ko" using
     patch_data/system_ko.json (RTK splits them per language)
  5. Map121/Map146: replace Show Text (401) params and choice (102) labels
     using patch_data/map_text_ko.json  (Japanese the devs left in the en slot)
  6. Every map: replace the strings the Korean slot actually shows using
     patch_data/map_ui_ko.json — bus fares, hint-terminal menu, rest/pay
     choices, script messages. Restricted to language-visible positions
     (tools/map_lang.py) so the ja/ch slots keep their own text.

Usage: uv run python tools/build_patch.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Pristine copies of the data files we patch. Never read the live game folder:
# once the patch is applied there, the Japanese source strings are gone and the
# substitutions silently match nothing.
GAME_DATA = ROOT / "source_data"
PATCH = ROOT / "patch"

sys.path.insert(0, str(ROOT / "tools"))
from map_lang import apply_to_visible, visible_pages  # noqa: E402
from sl_codec import xor_text  # noqa: E402


def encode_scenario() -> None:
    src = ROOT / "translated_ko"
    dst = PATCH / "scenario" / "En"
    dst.mkdir(parents=True, exist_ok=True)
    files = sorted(src.glob("*.txt"))
    for f in files:
        data = f.read_text(encoding="utf-8", newline="")
        # The originals use LF. An editor (or git autocrlf) may leave CRLF in
        # translated_ko; strip it so the engine never sees a stray \r.
        data = data.replace("\r\n", "\n")
        with open(dst / (f.stem + ".sl"), "w", encoding="utf-8", newline="") as out:
            out.write(xor_text(data))
    print(f"encoded {len(files)} scenario files")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8")


def load_table(name: str) -> dict[str, str]:
    """A patch_data lookup table; keys starting with '_' are comments."""
    return {k: v for k, v in load_json(ROOT / "patch_data" / name).items()
            if not k.startswith("_")}


def warn_unused(label: str, table: dict, used: set) -> None:
    unused = set(table) - used
    if unused:
        print(f"  WARN unused {label} translations: {len(unused)}")
        for u in sorted(unused)[:10]:
            print(f"    {u[:60]!r}")


def patch_common_events() -> None:
    cmap = load_json(ROOT / "patch_data" / "choices_ko.json")
    umap = load_table("event_ui_ko.json")
    data = load_json(GAME_DATA / "CommonEvents.json")
    hits = misses = 0

    def fix(s: str) -> str:
        nonlocal hits, misses
        parts = s.split(" ||| ")
        if len(parts) != 3:
            return s
        key = parts[0].strip() + "|||" + parts[2].strip()
        ko = cmap.get(key)
        if ko is None:
            misses += 1
            print(f"  WARN no choice translation: {key}")
            return s
        hits += 1
        return f"{parts[0]} ||| {ko} ||| {parts[2]}"

    for ev in data:
        if not ev:
            continue
        for cmd in ev.get("list") or []:
            if cmd["code"] == 102 and cmd["parameters"] and isinstance(cmd["parameters"][0], list):
                cmd["parameters"][0] = [fix(c) if isinstance(c, str) and " ||| " in c else c
                                        for c in cmd["parameters"][0]]
            elif cmd["code"] == 402 and len(cmd["parameters"]) > 1 and \
                    isinstance(cmd["parameters"][1], str) and " ||| " in cmd["parameters"][1]:
                cmd["parameters"][1] = fix(cmd["parameters"][1])

    # Choices the devs split into per-language conditional branches (variable 11)
    # instead of one "|||" string — same treatment as the maps get.
    used_ui: set[str] = set()
    n_ui = 0

    def ui(s: str):
        ko = umap.get(s)
        if ko is not None:
            used_ui.add(s)
        return ko

    for ev in data:
        if not ev:
            continue
        n_ui += apply_to_visible(ev.get("list") or [], ui)

    save_json(data, PATCH / "www" / "data" / "CommonEvents.json")
    print(f"CommonEvents: {hits} choice strings + {n_ui} branched choices "
          f"replaced, {misses} unmatched")
    warn_unused("event_ui", umap, used_ui)


def patch_db_notes() -> None:
    dmap = load_json(ROOT / "patch_data" / "db_en_ko.json")
    by_file: dict[str, dict[int, str]] = {}
    for key, ko in dmap.items():
        fname, oid = key.split("#")
        by_file.setdefault(fname, {})[int(oid)] = ko
    for fname, entries in by_file.items():
        data = load_json(GAME_DATA / f"{fname}.json")
        n = added = 0
        for o in data:
            if o and isinstance(o, dict) and o.get("id") in entries:
                note = o.get("note") or ""
                tag = "<en:" + entries[o["id"]] + ">"
                new_note, cnt = re.subn(r"<en:.*?>", lambda m: tag, note, count=1, flags=re.S)
                if cnt:
                    o["note"] = new_note
                else:
                    # Entries the devs never localized carry no <en:> tag at all
                    # (Armors#4/#11). Append one; RTK reads it from meta either way.
                    o["note"] = f"{note}\n{tag}" if note else tag
                    added += 1
                n += 1
        save_json(data, PATCH / "www" / "data" / f"{fname}.json")
        extra = f" ({added} <en:> tags added)" if added else ""
        print(f"{fname}: {n}/{len(entries)} notes replaced{extra}")


# plugins.js gives RTK1_Option_EnJa "separator": "||" — updateTypeData() splits every
# term-array entry on it and hands the halves to the ja / En slots.
LANG_SEPARATOR = "||"


def patch_system() -> None:
    """Term arrays carry both languages in one string: '持ち物||소지품'."""
    smap = load_table("system_ko.json")
    data = load_json(GAME_DATA / "System.json")
    n = 0
    for field, entries in smap.items():
        arr = data.get(field)
        if not isinstance(arr, list):
            print(f"  WARN System.{field}: not an array")
            continue
        for idx, ko in entries.items():
            i = int(idx)
            if i >= len(arr) or not isinstance(arr[i], str):
                print(f"  WARN System.{field}[{idx}]: missing")
                continue
            if LANG_SEPARATOR in arr[i]:
                print(f"  WARN System.{field}[{idx}]: already has a separator "
                      f"({arr[i]!r}) — source_data is not pristine")
                continue
            arr[i] = f"{arr[i]}{LANG_SEPARATOR}{ko}"
            n += 1
    save_json(data, PATCH / "www" / "data" / "System.json")
    print(f"System: {n} term entries given a Korean half")


# Maps where the devs left Japanese sitting in the en slot (hint terminal, salon…).
# Those strings are not language-branched, so they are replaced wherever they occur.
MAP_TEXT_MAPS = ("Map121", "Map146")


def patch_maps() -> None:
    """One pass per map: map_text_ko (untranslated Japanese) + map_ui_ko (en slot)."""
    mmap = load_json(ROOT / "patch_data" / "map_text_ko.json")
    umap = load_table("map_ui_ko.json")
    used_text: set[str] = set()
    used_ui: set[str] = set()

    def ui(s: str):
        ko = umap.get(s)
        if ko is not None:
            used_ui.add(s)
        return ko

    for src in sorted(GAME_DATA.glob("Map[0-9]*.json")):
        data = load_json(src)
        n_text = 0
        if src.stem in MAP_TEXT_MAPS:
            for ev in data.get("events") or []:
                if not ev:
                    continue
                for pg in ev.get("pages") or []:
                    for cmd in pg.get("list") or []:
                        if cmd["code"] == 401 and isinstance(cmd["parameters"][0], str):
                            s = cmd["parameters"][0]
                            if s in mmap:
                                cmd["parameters"][0] = mmap[s]
                                used_text.add(s)
                                n_text += 1
                        elif cmd["code"] == 102 and cmd["parameters"] and \
                                isinstance(cmd["parameters"][0], list):
                            newc = []
                            for c in cmd["parameters"][0]:
                                if isinstance(c, str) and c in mmap:
                                    newc.append(mmap[c])
                                    used_text.add(c)
                                    n_text += 1
                                else:
                                    newc.append(c)
                            cmd["parameters"][0] = newc

        n_ui = 0
        for ev in data.get("events") or []:
            if not ev:
                continue
            for pi in visible_pages(ev):
                n_ui += apply_to_visible(ev["pages"][pi].get("list") or [], ui)

        if n_text or n_ui or src.stem in MAP_TEXT_MAPS:
            save_json(data, PATCH / "www" / "data" / src.name)
            print(f"{src.stem}: {n_text} text + {n_ui} UI strings replaced")

    warn_unused("map", mmap, used_text)
    warn_unused("map_ui", umap, used_ui)


if __name__ == "__main__":
    encode_scenario()
    patch_common_events()
    patch_db_notes()
    patch_system()
    patch_maps()
