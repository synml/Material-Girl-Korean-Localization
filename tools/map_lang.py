"""Which map-event text does the Korean (en) slot actually show?

The maps localize in two ways, both keyed on variable 11 (■言語用変数), which
RTK1_Option_EnJa keeps in sync with ConfigManager.langSelect (0=ja, 1=en, 2=ch):

  1. conditional branch   111 [1, 11, 0, <lang>, 0]
  2. event page condition  variableId 11, variableValue <lang>
     (MV compares with >=, and runs the HIGHEST-numbered page whose
      conditions hold — so an unconditional page 0 is the ja fallback.)

Anything outside both mechanisms is language-independent: replacing it changes
every language, which is sometimes the only option (the game simply has no
translated variant) but must be a deliberate choice.
"""

import re

LANG = 1                       # the slot the Korean patch occupies
LANG_VARIABLE = 11
MSG_IN_SCRIPT = re.compile(r'(\$gameMessage\.add\(\s*")([^"]*)(")')


def _page_lang(page):
    c = page.get("conditions") or {}
    if c.get("variableValid") and c.get("variableId") == LANG_VARIABLE:
        return c.get("variableValue")
    return None


def _has_other_conditions(page) -> bool:
    c = page.get("conditions") or {}
    if any(c.get(k) for k in ("switch1Valid", "switch2Valid", "selfSwitchValid",
                              "itemValid", "actorValid")):
        return True
    return bool(c.get("variableValid")) and c.get("variableId") != LANG_VARIABLE


def visible_pages(event) -> list[int]:
    """Page indexes that can run when variable 11 == LANG."""
    out = []
    for pi in range(len(event["pages"]) - 1, -1, -1):
        page = event["pages"][pi]
        pl = _page_lang(page)
        if pl is not None and pl > LANG:
            continue                       # needs a higher language id
        out.append(pi)
        if not _has_other_conditions(page):
            break                          # always wins over the pages below it
    return sorted(out)


def apply_to_visible(page_list, fn) -> int:
    """Call fn(text) on every displayed string the Korean slot can reach.

    fn returns a replacement string, or None to leave it alone.
    Returns the number of replacements made (page_list is mutated in place).
    """
    n = 0
    stack: list[tuple[int, object]] = []

    def sub(s):
        nonlocal n
        new = fn(s)
        if new is None or new == s:
            return s
        n += 1
        return new

    for cmd in page_list:
        ind, code, ps = cmd["indent"], cmd["code"], cmd["parameters"]
        while stack and ind <= stack[-1][0]:
            stack.pop()
        if code == 111 and len(ps) >= 4 and ps[0] == 1 and ps[1] == LANG_VARIABLE:
            stack.append((ind, ps[3]))
            continue
        if code == 411:                    # Else of a language branch
            if stack and stack[-1][0] == ind:
                stack.pop()
            stack.append((ind, "else"))
            continue
        lang = stack[-1][1] if stack else None
        if lang not in (None, LANG, "else"):
            continue                       # another language's branch
        if code in (401, 405) and isinstance(ps[0], str):
            ps[0] = sub(ps[0])
        elif code == 102 and ps and isinstance(ps[0], list):
            ps[0] = [sub(c) if isinstance(c, str) else c for c in ps[0]]
        elif code in (320, 324, 325):
            cmd["parameters"] = [sub(p) if isinstance(p, str) else p for p in ps]
        elif code in (355, 655) and isinstance(ps[0], str):
            # message text embedded in a script call
            ps[0] = MSG_IN_SCRIPT.sub(lambda m: m.group(1) + sub(m.group(2)) + m.group(3), ps[0])
    return n
