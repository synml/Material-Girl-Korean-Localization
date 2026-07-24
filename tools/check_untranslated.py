"""Sweep every surface the Korean slot can display and report untranslated text.

The other checkers only look at translated_ko (review_scan, verify_translation,
check_line_width). This one covers what lives outside it:

  1. strings the En slot shows with no Hangul at all (CommonEvents + every map),
     including the choices the devs branched on the language variable instead of
     packing into one "ja ||| en ||| ch" string
  2. map notes -> TS_Localize.ChangeList (the save/load screen's location label)
  3. ExpStatus partner names -> ChangeList (the status screen's first/last name)
  4. database rows with no <en:> tag that the game actually uses
  5. System.json term arrays with no Korean half ("ja||ko")

Patched files are read from patch/www/data; everything else from the installed
game (data the patch does not touch is still pristine there). Without the game
folder the sweep still runs, but axes limited to unpatched files are skipped.

Usage: uv run python tools/check_untranslated.py [game_dir]
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATCHED = ROOT / "patch" / "www" / "data"
DEFAULT_GAME = Path(r"D:\SteamLibrary\steamapps\common\Material Girl")

sys.path.insert(0, str(ROOT / "tools"))
from map_lang import apply_to_visible, visible_pages  # noqa: E402

HANGUL = re.compile(r"[가-힣]")
WORD = re.compile(r"[A-Za-z\u3040-\u30ff\u4e00-\u9fff\uff21-\uff3a\uff41-\uff5a]")
EXPSTATUS = re.compile(r"ExpStatus[^\\\"\n]*")

# Deliberately left as-is (CLAUDE.md §5-1) — "file/event: string".
ALLOW_NO_HANGUL = {
    ("Map010", "選択肢1"), ("Map010", "選択肢2"), ("Map010", "選択肢3"),
    ("Map010", "<limit:5>"),          # 스위치로만 열리는 디버그 이벤트 + 플러그인 태그
    ("Map121", "CG03"), ("Map121", "CG10"), ("Map121", "CG13"),
    ("Map121", "CG16"), ("Map121", "CG18"),   # CG 번호 선택지
}

findings: list[str] = []
notes: list[str] = []


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def data_file(name: str, game_data: Path | None) -> Path | None:
    """The build output if we patch this file, else the pristine game copy."""
    p = PATCHED / name
    if p.exists():
        return p
    if game_data:
        p = game_data / name
        if p.exists():
            return p
    return None


def change_list_keys() -> set[str]:
    js = (ROOT / "patch" / "www" / "js" / "plugins" / "TS_Localize.js").read_text(encoding="utf-8")
    block = js.split("TS_Localize.ChangeList = {")[1].split("\n}")[0]
    return set(re.findall(r"^\s*'([^']+)'\s*:\s*\[", block, re.M))


def event_lists(data):
    """(label, command list) for every page of every event / common event."""
    if isinstance(data, dict):                      # map
        for ev in data.get("events") or []:
            if not ev:
                continue
            for pi in visible_pages(ev):
                yield f"ev{ev['id']}", ev["pages"][pi].get("list") or []
    else:                                           # CommonEvents
        for ev in data:
            if ev and isinstance(ev, dict):
                yield f"ev{ev['id']}", ev.get("list") or []


def check_visible_strings(files: list[tuple[str, Path]]) -> None:
    for stem, path in files:
        for label, cmds in event_lists(load(path)):
            seen: list[str] = []
            apply_to_visible(cmds, lambda s: seen.append(s) or None)
            for s in seen:
                t = s.strip()
                if not t or HANGUL.search(t) or not WORD.search(t):
                    continue
                if " ||| " in t:                    # 3-language string: check the En slot
                    t = t.split(" ||| ")[1].strip()
                    if not t or HANGUL.search(t):
                        continue
                if (stem, t) in ALLOW_NO_HANGUL:
                    continue
                findings.append(f"[한글 없음] {stem}/{label}\t{t[:100]!r}")


def check_map_notes(map_files: list[tuple[str, Path]], keys: set[str]) -> None:
    for stem, path in map_files:
        note = (load(path).get("note") or "").strip()
        if note and note not in keys:
            findings.append(f"[세이브 화면 지역명 미등록] {stem}\t{note!r}")


def check_partner_names(files: list[tuple[str, Path]], keys: set[str]) -> None:
    seen: dict[str, str] = {}
    sources = [(stem, path.read_text(encoding="utf-8-sig")) for stem, path in files]
    sources += [(p.stem, p.read_text(encoding="utf-8")) for p in (ROOT / "source_en").glob("*.txt")]
    for stem, text in sources:
        for m in EXPSTATUS.finditer(text):
            tok = m.group(0).split()
            if len(tok) >= 5 and tok[2].upper() in ("MOUTH", "BREAST", "SEX"):
                seen.setdefault(tok[4], stem)
    for name, where in sorted(seen.items()):
        if name not in keys:
            findings.append(f"[스테이터스 상대 이름 미등록] {where}\t{name!r}")


def used_db_ids(files: list[tuple[str, Path]]) -> dict[str, set[int]]:
    """Which Items/Weapons/Armors/Actors ids the events actually touch."""
    used: dict[str, set[int]] = {k: set() for k in ("Items", "Weapons", "Armors", "Actors")}
    used["_battle"] = set()
    for _, path in files:
        data = load(path)
        for _, cmds in event_lists(data):
            for c in cmds:
                code, ps = c.get("code"), c.get("parameters") or []
                if code == 126:
                    used["Items"].add(ps[0])
                elif code == 127:
                    used["Weapons"].add(ps[0])
                elif code == 128:
                    used["Armors"].add(ps[0])
                elif code == 129 and len(ps) > 1 and ps[1] == 0:
                    used["Actors"].add(ps[0])
                elif code == 319 and len(ps) > 2:
                    # slot 1 holds weapons, every other slot holds armors.
                    # Equipping an actor says nothing about whether the actor is
                    # ever displayed — only "add party member" (129) does.
                    used["Weapons" if ps[1] == 1 else "Armors"].add(ps[2])
                elif code == 301:
                    used["_battle"].add(1)
    return used


def check_db_notes(files: list[tuple[str, Path]], game_data: Path | None) -> None:
    used = used_db_ids(files)
    sysfile = data_file("System.json", game_data)
    if sysfile:
        used["Actors"] |= set(load(sysfile).get("partyMembers") or [])
    # Actor classes are reachable exactly when their actor is
    actorfile = data_file("Actors.json", game_data)
    if actorfile:
        used["Classes"] = {o["classId"] for o in load(actorfile)
                           if o and isinstance(o, dict) and o["id"] in used["Actors"]}
    # Battle-only tables: dead while the game never runs a battle
    battle_only = ("Skills", "States", "Enemies", "Troops")
    for name in ("Actors", "Classes", "Items", "Weapons", "Armors") + battle_only:
        path = data_file(f"{name}.json", game_data)
        if not path:
            continue
        if name in battle_only and not used["_battle"]:
            continue
        for o in load(path):
            if not o or not isinstance(o, dict) or not (o.get("name") or "").strip():
                continue
            if "<en:" in (o.get("note") or ""):
                continue
            if name in used and o["id"] not in used[name]:
                continue        # never given, equipped or joined — dead row
            findings.append(f"[<en:> 없음] {name}#{o['id']}\t{o['name']!r}")


def check_system_terms(game_data: Path | None) -> None:
    path = data_file("System.json", game_data)
    if not path:
        notes.append("System.json 없음 — 용어 배열 검사 생략")
        return
    data = load(path)
    table = json.loads((ROOT / "patch_data" / "system_ko.json").read_text(encoding="utf-8"))
    for field in [k for k in table if not k.startswith("_")]:
        for i, v in enumerate(data.get(field) or []):
            if i and isinstance(v, str) and v and "||" not in v:
                findings.append(f"[한국어 절반 없음] System.{field}[{i}]\t{v!r}")


def main() -> None:
    game = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_GAME
    game_data = game / "www" / "data"
    if not game_data.is_dir():
        game_data = None
        notes.append(f"게임 폴더 없음({game}) — 패치 대상 외 맵/DB는 검사에서 빠진다")

    names = sorted({p.name for p in PATCHED.glob("*.json")} |
                   ({p.name for p in game_data.glob("*.json")} if game_data else set()))
    maps = [(n[:-5], data_file(n, game_data)) for n in names
            if n.startswith("Map") and n != "MapInfos.json"]
    maps = [(s, p) for s, p in maps if p]
    events = maps[:]
    ce = data_file("CommonEvents.json", game_data)
    if ce:
        events.append(("CommonEvents", ce))

    keys = change_list_keys()
    check_visible_strings(events)
    check_map_notes(maps, keys)
    check_partner_names(events, keys)
    check_db_notes(events, game_data)
    check_system_terms(game_data)

    out = ROOT / "review" / "untranslated_report.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(findings), encoding="utf-8")
    for line in notes:
        print(f"note: {line}")
    print(f"{len(findings)} issues -> {out}")


if __name__ == "__main__":
    main()
